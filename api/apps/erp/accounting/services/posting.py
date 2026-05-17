from sqlalchemy.orm import Session
from ..models import InflowInvoice, OutflowInvoice
from .journal import JournalService
from ...stock.services.coa_resolver import CoaResolver
from ...stock.services.uom import UomService
from ...stock.services.valuation import InventoryValuationService # Import valuation service

def _create_stock_movement(db: Session, invoice_number: str, org_id: int, move_type: str, lines_data: list[dict]) -> None:
    """Create a Posted StockMovement from invoice lines — only when perpetual inventory is enabled."""
    from ...stock.models import StockMovement, StockMovementLine, Location
    from ...config.models import Organization
    co = db.get(Organization, org_id)
    if not co or not co.enable_perpetual_inventory:
        return
    loc = db.query(Location).filter_by(org_id=org_id, location_type="Internal").first()
    loc_id = loc.id if loc else None
    sm_move_type = "receipt" if move_type == "Incoming" else "delivery"
    movement = StockMovement(
        org_id=org_id,
        number=f"SM-{invoice_number}",
        move_type=sm_move_type,
        status="Posted",
        from_location_id=loc_id if move_type == "Outgoing" else None,
        to_location_id=loc_id if move_type == "Incoming" else None,
    )
    db.add(movement)
    db.flush()
    from ...stock.models import Item
    for ld in lines_data:
        item = db.get(Item, ld["product_id"])
        base_uom_id = item.uom_id if item else ld["uom_id"]
        qty_base = UomService.convert_qty(db, ld["product_id"], ld["qty"], ld["uom_id"], base_uom_id) if ld["uom_id"] and ld["uom_id"] != base_uom_id else ld["qty"]
        ml = StockMovementLine(
            movement_id=movement.id,
            item_id=ld["product_id"],
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
            rev_account = CoaResolver.resolve_revenue_account(db, inv_line.item_id, org_id)
            if not rev_account:
                return {"error": f"Revenue account not found for item {inv_line.item_id}"}
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
            journal_entry = JournalService.post_entry( # Store journal_entry for consistent return
                db, org_id, lines,
                reference=invoice.number,
                narrative=f"Auto-posted from Inflow Invoice {invoice.number}",
                currency_id=invoice.currency_id,
            )
            # For each inflow invoice line, we need to consume stock for COGS
            stock_movement_lines_data = []
            for l in invoice.lines:
                cogs = InventoryValuationService.consume(db, l.item_id, org_id, l.qty)
                stock_movement_lines_data.append({
                    "product_id": l.item_id,
                    "qty": l.qty,
                    "uom_id": l.uom_id,
                    "unit_cost": cogs / l.qty if l.qty else 0
                })
            _create_stock_movement(db, invoice.number, org_id, "Outgoing", stock_movement_lines_data)
            invoice.status = "Posted"
            db.commit()
            return {"success": True, "message": "Inflow Invoice posted successfully.", "journal_entry_id": journal_entry.id}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": str(e), "journal_entry_id": None}

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
            cogs_account = CoaResolver.resolve_cogs_account(db, inv_line.item_id, org_id)
            if not cogs_account:
                return {"error": f"Expense/COGS account not found for item {inv_line.item_id}"}

            # --- COGS calculation using FIFO valuation ---
            cost_of_goods_sold = InventoryValuationService.consume(db, inv_line.item_id, org_id, inv_line.qty)
            
            lines.append({
                "account_id": cogs_account.id,
                "debit": cost_of_goods_sold,
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
            journal_entry = JournalService.post_entry( # Store journal_entry for consistent return
                db, org_id, lines,
                reference=invoice.number,
                narrative=f"Auto-posted from Outflow Invoice {invoice.number}",
                currency_id=invoice.currency_id,
            )
            # If a GRN is linked, the stock movement has already been created there.
            # If no GRN, and this is an incoming transaction, use valuation service to 'receive' stock.
            # This logic needs to be carefully aligned with actual stock movements.
            # The _create_stock_movement here is for tracking 'movements', not for creating valuation layers.
            # Stock layers are created when GRNs are posted.
            if not invoice.grn_id:
                _create_stock_movement(db, invoice.number, org_id, "Incoming", [
                    {"product_id": l.item_id, "qty": l.qty, "uom_id": l.uom_id, "unit_cost": l.unit_price - l.discount}
                    for l in invoice.lines
                ])
            
            invoice.status = "Posted"
            db.commit()
            return {"success": True, "message": "Outflow Invoice posted successfully.", "journal_entry_id": journal_entry.id}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": str(e), "journal_entry_id": None}
