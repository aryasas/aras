"""
Workflow handlers for accounting documents.
Registered in HandlerRegistry so they can be triggered by WorkflowManager
(DB-driven templates) or called directly from model actions.
"""
from sqlalchemy.orm import Session
from core.logic.handler_registry import HandlerRegistry
from core.manager.naming_manager import SeriesManager


@HandlerRegistry.register(
    "post_stock_movement",
    "Create StockMovement from invoice lines (InflowInvoice→Outgoing, OutflowInvoice→Incoming). "
    "Skipped when perpetual inventory is disabled or GRN already created the movement."
)
def post_stock_movement(db: Session, item, params: dict):
    from ..config.models import Organization
    from ..stock.models import StockMovement, StockMovementLine, Location, Item
    from ..stock.services.uom import UomService
    from ..stock.services.valuation import InventoryValuationService
    from .models import InflowInvoice, OutflowInvoice

    org = db.get(Organization, item.org_id)
    if not org or not org.enable_perpetual_inventory:
        return

    if isinstance(item, OutflowInvoice) and item.grn_id:
        return  # GRN already created the incoming movement

    if isinstance(item, InflowInvoice):
        move_type = "delivery"
        loc_field = "from_location_id"
    elif isinstance(item, OutflowInvoice):
        move_type = "receipt"
        loc_field = "to_location_id"
    else:
        return

    loc = db.query(Location).filter_by(org_id=item.org_id, location_type="Internal").first()
    loc_id = loc.id if loc else None

    movement = StockMovement(
        org_id=item.org_id,
        number=SeriesManager.get_next(db, "erp_stock_movements"),
        move_type=move_type,
        status="Posted",
        origin_model=item.__class__.__name__,
        origin_id=item.id,
        **{loc_field: loc_id},
    )
    db.add(movement)
    db.flush()
    item.stock_movement_id = movement.id

    for line in item.lines:
        item_obj = db.get(Item, line.item_id)
        if not item_obj or not item_obj.is_stock_item:
            continue

        base_uom_id = item_obj.uom_id
        qty = float(line.qty)
        qty_base = (
            UomService.convert_qty(db, line.item_id, qty, line.uom_id, base_uom_id)
            if line.uom_id and line.uom_id != base_uom_id
            else qty
        )

        if move_type == "delivery":
            total_cost = InventoryValuationService.consume(db, line.item_id, item.org_id, qty_base)
            unit_cost = total_cost / qty_base if qty_base else 0
            sm_line = StockMovementLine(
                movement_id=movement.id,
                item_id=line.item_id,
                qty=qty_base,
                uom_id=base_uom_id,
                unit_cost=unit_cost,
                total_cost=total_cost,
                from_location_id=loc_id,
            )
        else:
            unit_cost = float(line.unit_price - line.discount)
            sm_line = StockMovementLine(
                movement_id=movement.id,
                item_id=line.item_id,
                qty=qty_base,
                uom_id=base_uom_id,
                unit_cost=unit_cost,
                qty_remaining=qty_base,
                to_location_id=loc_id,
            )
            db.add(sm_line)
            db.flush()
            InventoryValuationService.receive(
                db, line.item_id, item.org_id, qty_base, unit_cost,
                source_line_id=sm_line.id,
            )
            continue

        db.add(sm_line)


@HandlerRegistry.register(
    "post_journal_entry",
    "Create JournalEntry from invoice lines. InflowInvoice: DR AR / CR Revenue. OutflowInvoice: DR Stock/Expense / CR AP."
)
def post_journal_entry(db: Session, item, params: dict):
    from .models import InflowInvoice, OutflowInvoice
    from .services.journal import JournalService
    from ..stock.services.coa_resolver import CoaResolver

    org_id = item.org_id
    lines = []

    if isinstance(item, InflowInvoice):
        ar_account = CoaResolver.resolve_ar_account(db, org_id)
        if not ar_account:
            raise ValueError("AR account not configured for this org.")

        lines.append({
            "account_id": ar_account.id,
            "debit": float(item.total_amount),
            "credit": 0,
            "description": f"Inflow Invoice {item.number}",
        })
        for inv_line in item.lines:
            rev = CoaResolver.resolve_revenue_account(db, inv_line.item_id, org_id)
            if not rev:
                raise ValueError(f"Revenue account not found for item {inv_line.item_id}")
            line_total = float(inv_line.qty) * float(inv_line.unit_price - inv_line.discount)
            lines.append({
                "account_id": rev.id,
                "debit": 0,
                "credit": line_total,
                "description": f"Revenue {item.number}",
            })
        for charge in item.charges:
            _append_charge_line(db, charge, lines, side="credit")

        entry = JournalService.post_entry(
            db, org_id, lines,
            reference=item.number,
            narrative=f"Auto-posted from Inflow Invoice {item.number}",
            currency_id=item.currency_id,
            source_type="InflowInvoice",
            source_id=item.id,
        )
        item.journal_entry_id = entry.id

    elif isinstance(item, OutflowInvoice):
        from ..stock.models import Item as StockItem
        for inv_line in item.lines:
            product = db.get(StockItem, inv_line.item_id)
            if product and product.is_stock_item:
                acct = CoaResolver.resolve_stock_account(db, inv_line.item_id, org_id)
                acc_label = "Stock"
            else:
                acct = CoaResolver.resolve_expense_account(db, inv_line.item_id, org_id)
                acc_label = "Expense"
            if not acct:
                raise ValueError(f"{acc_label} account not found for item {inv_line.item_id}")
            line_total = float(inv_line.qty) * float(inv_line.unit_price - inv_line.discount)
            lines.append({
                "account_id": acct.id,
                "debit": line_total,
                "credit": 0,
                "description": f"Purchase {item.number}",
            })
        for charge in item.charges:
            _append_charge_line(db, charge, lines, side="debit")

        ap_account = CoaResolver.resolve_ap_account(db, org_id)
        if not ap_account:
            raise ValueError("AP account not configured for this org.")
        lines.append({
            "account_id": ap_account.id,
            "debit": 0,
            "credit": float(item.total_amount),
            "description": f"Outflow Invoice {item.number}",
        })
        entry = JournalService.post_entry(
            db, org_id, lines,
            reference=item.number,
            narrative=f"Auto-posted from Outflow Invoice {item.number}",
            currency_id=item.currency_id,
            source_type="OutflowInvoice",
            source_id=item.id,
        )
        item.journal_entry_id = entry.id


def _append_charge_line(db, charge, lines: list, side: str):
    from ..config.models import Charge
    charge_def = db.get(Charge, charge.charge_id)
    if not charge_def:
        return
    acct_id = charge_def.account_collected_id if side == "credit" else charge_def.account_paid_id
    if acct_id:
        lines.append({
            "account_id": acct_id,
            "debit": 0 if side == "credit" else float(charge.amount),
            "credit": float(charge.amount) if side == "credit" else 0,
            "description": f"Charge: {charge_def.name}",
        })
    elif lines:
        lines[-1][side] = float(lines[-1][side]) + float(charge.amount)
