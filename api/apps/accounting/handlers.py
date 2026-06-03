"""
Workflow handlers for accounting documents.
Registered in HandlerRegistry so they can be triggered by WorkflowManager
(DB-driven templates) or called directly from model actions.
"""
from sqlalchemy.orm import Session
from core.logic.handler_registry import HandlerRegistry
from core.manager.naming_manager import SeriesManager
from core.lib import math_utils


@HandlerRegistry.register(
    "post_stock_movement",
    "Create StockMovement from invoice lines (InflowInvoice→Outgoing, OutflowInvoice→Incoming). "
    "Skipped when perpetual inventory is disabled or GRN already created the movement."
)
def post_stock_movement(db: Session, item, params: dict):
    from apps.config.models import Organization
    from apps.stock.models import StockMovement, StockMovementLine, Location, Item
    from apps.stock.services.uom import UomService
    from apps.stock.services.valuation import InventoryValuationService

    org = db.get(Organization, item.org_id)
    if not org or not org.enable_perpetual_inventory:
        return

    if getattr(item, "grn_id", None):
        return  # GRN already created the incoming movement

    try:
        move_type = item.get_stock_movement_type()
    except (AttributeError, NotImplementedError):
        return

    loc_field = "from_location_id" if move_type == "delivery" else "to_location_id"

    loc = db.query(Location).filter_by(org_id=item.org_id, location_type="Internal").first()
    loc_id = loc.id if loc else None

    movement = StockMovement(
        org_id=item.org_id,
        number=SeriesManager.get_next(db, "stock_movements"),
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
            unit_cost = math_utils.line_total(1.0, line.unit_price, line.discount)
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
    "Create JournalEntry from invoice lines using TradeDocumentBase methods."
)
def post_invoice_gl(db: Session, item, params: dict):
    from .services.journal import JournalService
    from apps.stock.services.coa_resolver import CoaResolver
    from core.registry.settings_service import SettingsService
    if not SettingsService.get(db, "accounting", "enable_auto_journal", True):
        return

    org_id = item.org_id
    gl_side = item.get_gl_side()  # credit for Sales, debit for Purchase
    payment_type = item.get_payment_type()  # receivable for Sales, payable for Purchase
    lines = []

    # 1. Primary lines (Revenue or Stock/Expense)
    for inv_line in item.lines:
        if payment_type == "receivable":
            acct = CoaResolver.resolve_revenue_account(db, inv_line.item_id, org_id)
        else:
            from apps.stock.models import Item as StockItem
            product = db.get(StockItem, inv_line.item_id)
            if product and product.is_stock_item:
                acct = CoaResolver.resolve_stock_account(db, inv_line.item_id, org_id)
            else:
                acct = CoaResolver.resolve_expense_account(db, inv_line.item_id, org_id)

        if not acct:
            raise ValueError(f"Account not found for item {inv_line.item_id}")
        
        line_total = math_utils.line_total(inv_line.qty, inv_line.unit_price, inv_line.discount)
        lines.append({
            "account_id": acct.id,
            "debit": line_total if gl_side == "debit" else 0,
            "credit": line_total if gl_side == "credit" else 0,
            "description": f"Line: {item.number}",
        })

    # 2. Charges
    for charge in item.charges:
        _append_charge_line(db, charge, lines, side=gl_side)

    # 3. Offset line (AR or AP or Cash)
    payment_account_id = params.get("payment_account_id")
    payment = params.get("payment")

    if payment_account_id and payment_type == "receivable":
        # Cash/immediate-payment sale logic (InflowInvoice)
        total_credit = sum(l["credit"] for l in lines)
        amount_paid_param = float(params.get("amount_paid", total_credit))

        if amount_paid_param < total_credit:
            ar_account = CoaResolver.resolve_ar_account(db, org_id)
            if not ar_account: raise ValueError("AR account not configured.")
            lines.insert(0, {
                "account_id": ar_account.id,
                "debit": round(total_credit - amount_paid_param, 10),
                "credit": 0,
                "description": f"Partial receivable {item.number}",
            })
            lines.insert(0, {
                "account_id": payment_account_id,
                "debit": amount_paid_param,
                "credit": 0,
                "description": f"Partial payment received {item.number}",
            })
        else:
            lines.insert(0, {
                "account_id": payment_account_id,
                "debit": total_credit,
                "credit": 0,
                "description": f"Payment received {item.number}",
            })
    else:
        # Standard Credit sale or Purchase
        if payment_type == "receivable":
            offset_acct = CoaResolver.resolve_ar_account(db, org_id)
        else:
            offset_acct = CoaResolver.resolve_ap_account(db, org_id)
        
        if not offset_acct:
            raise ValueError(f"{payment_type.capitalize()} account not configured.")

        total_amount = float(item.total_amount)
        lines.append({
            "account_id": offset_acct.id,
            "debit": 0 if gl_side == "debit" else total_amount,
            "credit": total_amount if gl_side == "debit" else 0,
            "description": f"{payment_type.capitalize()} {item.number}",
        })

    entry = JournalService.post_entry(
        db, org_id, lines,
        reference=item.number,
        narrative=f"Auto-posted from {item.__class__.__name__} {item.number}",
        currency_id=item.currency_id,
        source_type=item.__class__.__name__,
        source_id=item.id,
    )
    item.journal_entry_id = entry.id
    if payment is not None:
        payment.journal_entry_id = entry.id


def _append_charge_line(db, charge, lines: list, side: str):
    from apps.config.models import Charge
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
