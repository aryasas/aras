from sqlalchemy.orm import Session
from ..models import InflowInvoice, OutflowInvoice
from .journal import JournalService
from ...stock.services.coa_resolver import CoaResolver
from ...stock.services.uom import UomService


def _create_stock_movement(db: Session, invoice_number: str, org_id: int, move_type: str, lines_data: list[dict], currency_id: int = None) -> None:
    """Create a Posted StockMovement from invoice lines — only when perpetual inventory is enabled."""
    from ...stock.models import StockMovement, StockMovementLine, Location
    from ...config.models import Organization, Currency
    co = db.get(Organization, org_id)
    if not co or not co.enable_perpetual_inventory:
        return
    loc = db.query(Location).filter_by(org_id=org_id, location_type="Internal").first()
    if not currency_id:
        currency_id = co.base_currency_id or (db.query(Currency).first().id if db.query(Currency).first() else None)
    movement = StockMovement(
        org_id=org_id,
        number=f"SM-{invoice_number}",
        move_type=move_type,
        currency_id=currency_id,
        status="Posted",
        from_location_id=loc.id if move_type == "Outgoing" else None,
        to_location_id=loc.id if move_type == "Incoming" else None,
    )
    db.add(movement)
    db.flush()
    from ...stock.models import Product
    for ld in lines_data:
        product = db.get(Product, ld["product_id"])
        base_uom_id = product.uom_id if product else ld["uom_id"]
        qty_base = UomService.convert_qty(db, ld["product_id"], ld["qty"], ld["uom_id"], base_uom_id) if ld["uom_id"] and ld["uom_id"] != base_uom_id else ld["qty"]
        ml = StockMovementLine(
            movement_id=movement.id,
            product_id=ld["product_id"],
            qty=qty_base,
            uom_id=base_uom_id,
            unit_cost=ld.get("unit_cost", 0),
            from_location_id=loc.id if move_type == "Outgoing" else None,
            to_location_id=loc.id if move_type == "Incoming" else None,
        )
        db.add(ml)


class InvoicePostingService:
    @staticmethod
    def post_inflow_invoice(db: Session, invoice: InflowInvoice):
        if invoice.status != "Draft":
            return {"error": f"Invoice is already {invoice.status}"}

        org_id = invoice.org_id
        ar_account = CoaResolver.resolve_ar_account(db, org_id)
        if not ar_account:
            return {"error": "AR account not found. Please configure a non-group Asset account."}

        lines = [{
            "account_id": ar_account.id,
            "debit": invoice.total_amount,
            "credit": 0,
            "description": f"Inflow Invoice {invoice.number}"
        }]

        # Revenue lines — per invoice line product
        for inv_line in invoice.lines:
            rev_account = CoaResolver.resolve_revenue_account(db, inv_line.product_id, org_id)
            if not rev_account:
                return {"error": f"Revenue account not found for product {inv_line.product_id}"}
            line_total = inv_line.qty * (inv_line.unit_price - inv_line.discount)
            lines.append({
                "account_id": rev_account.id,
                "debit": 0,
                "credit": line_total,
                "description": f"Inflow Revenue from {invoice.number}"
            })

        # Charge lines
        for charge_line in invoice.charges:
            from ..config.models import Charge
            charge_def = db.query(Charge).get(charge_line.charge_id)
            if charge_def and charge_def.account_collected_id:
                lines.append({
                    "account_id": charge_def.account_collected_id,
                    "debit": 0,
                    "credit": charge_line.amount,
                    "description": f"Charge: {charge_def.name}"
                })
            elif lines:
                # Fallback: add to last revenue line
                lines[-1]["credit"] += charge_line.amount

        try:
            JournalService.post_entry(
                db, org_id, lines,
                reference=invoice.number,
                narrative=f"Auto-posted from Inflow Invoice {invoice.number}",
                currency_id=invoice.currency_id,
            )
            _create_stock_movement(db, invoice.number, org_id, "Outgoing", [
                {"product_id": l.product_id, "qty": l.qty, "uom_id": l.uom_id, "unit_cost": l.unit_price - l.discount}
                for l in invoice.lines
            ], currency_id=invoice.currency_id)
            invoice.status = "Posted"
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return {"error": str(e)}

    @staticmethod
    def post_outflow_invoice(db: Session, invoice: OutflowInvoice):
        if invoice.status != "Draft":
            return {"error": f"Invoice is already {invoice.status}"}

        org_id = invoice.org_id
        ap_account = CoaResolver.resolve_ap_account(db, org_id)
        if not ap_account:
            return {"error": "AP account not found. Please configure a non-group Liability account."}

        lines = []

        # Expense lines — per invoice line product
        for inv_line in invoice.lines:
            cogs_account = CoaResolver.resolve_cogs_account(db, inv_line.product_id, org_id)
            if not cogs_account:
                return {"error": f"Expense/COGS account not found for product {inv_line.product_id}"}
            line_total = inv_line.qty * (inv_line.unit_price - inv_line.discount)
            lines.append({
                "account_id": cogs_account.id,
                "debit": line_total,
                "credit": 0,
                "description": f"Outflow Expense from {invoice.number}"
            })

        # Charge lines
        for charge_line in invoice.charges:
            from ..config.models import Charge
            charge_def = db.query(Charge).get(charge_line.charge_id)
            if charge_def and charge_def.account_paid_id:
                lines.append({
                    "account_id": charge_def.account_paid_id,
                    "debit": charge_line.amount,
                    "credit": 0,
                    "description": f"Charge: {charge_def.name}"
                })
            elif lines:
                lines[0]["debit"] += charge_line.amount

        # AP Credit
        lines.append({
            "account_id": ap_account.id,
            "debit": 0,
            "credit": invoice.total_amount,
            "description": f"Outflow Invoice {invoice.number}"
        })

        try:
            JournalService.post_entry(
                db, org_id, lines,
                reference=invoice.number,
                narrative=f"Auto-posted from Outflow Invoice {invoice.number}",
                currency_id=invoice.currency_id,
            )
            _create_stock_movement(db, invoice.number, org_id, "Incoming", [
                {"product_id": l.product_id, "qty": l.qty, "uom_id": l.uom_id, "unit_cost": l.unit_price - l.discount}
                for l in invoice.lines
            ], currency_id=invoice.currency_id)
            invoice.status = "Posted"
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return {"error": str(e)}
 str(e)}
