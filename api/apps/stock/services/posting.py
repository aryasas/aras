from core import Aras
from sqlalchemy.orm import Session
from ..models import StockMovement, StockMovementLine, ItemBundle
from sqlalchemy import func
from decimal import Decimal


@Aras.on_transition(StockMovement, from_="Draft", to="Posted")
def post_stock_movement(db: Session, item, user, transition):
    movement: StockMovement = item
    _expand_bundles(db, movement)
    db.flush()

    lines = db.query(StockMovementLine).filter(StockMovementLine.movement_id == movement.id).all()
    journal_lines = []

    for line in lines:
        from ..models import Item as StockItem
        item_obj = db.get(StockItem, line.item_id)
        if not item_obj or not item_obj.is_stock_item:
            continue

        unit_cost = float(line.unit_cost or 0)

        if movement.move_type in ("receipt", "return"):
            prev_qty = _net_qty(db, line.item_id, exclude_id=movement.id)
            prev_cost = _last_avg_cost(db, line.item_id)
            in_qty = float(line.qty)
            new_qty = prev_qty + in_qty
            running_avg = ((prev_qty * prev_cost) + (in_qty * unit_cost)) / new_qty if new_qty else unit_cost
            line.running_avg_cost = running_avg
            line.total_cost = in_qty * running_avg

            from .valuation import InventoryValuationService
            InventoryValuationService.receive(
                db, item_obj.id, movement.org_id, in_qty, unit_cost,
                source_line_id=line.id
            )

            stock_acct, purchase_acct = _accounts_for_in(db, item_obj, movement.org_id)
            if stock_acct and purchase_acct:
                journal_lines += [
                    {"account_id": stock_acct.id, "debit": float(line.total_cost), "credit": 0},
                    {"account_id": purchase_acct.id, "debit": 0, "credit": float(line.total_cost)},
                ]

        elif movement.move_type == "delivery":
            from .valuation import InventoryValuationService
            consumed = InventoryValuationService.consume(db, item_obj.id, movement.org_id, float(line.qty))
            line.total_cost = consumed
            line.running_avg_cost = consumed / float(line.qty) if line.qty else 0

            cogs_acct, stock_acct = _accounts_for_out(db, item_obj, movement.org_id)
            if cogs_acct and stock_acct:
                journal_lines += [
                    {"account_id": cogs_acct.id, "debit": consumed, "credit": 0},
                    {"account_id": stock_acct.id, "debit": 0, "credit": consumed},
                ]

        elif movement.move_type == "scrap":
            from .valuation import InventoryValuationService
            consumed = InventoryValuationService.consume(db, item_obj.id, movement.org_id, float(line.qty))
            line.total_cost = consumed

            variance_acct, stock_acct = _accounts_for_scrap(db, item_obj, movement.org_id)
            if variance_acct and stock_acct:
                journal_lines += [
                    {"account_id": variance_acct.id, "debit": consumed, "credit": 0},
                    {"account_id": stock_acct.id, "debit": 0, "credit": consumed},
                ]

    if journal_lines:
        from apps.accounting.services.journal import JournalService
        entry = JournalService.post_entry(
            db=db, org_id=movement.org_id, reference=movement.number,
            lines=journal_lines,
        )
        movement.journal_entry_id = entry.id


def _expand_bundles(db: Session, movement: StockMovement):
    from ..models import Item as StockItem
    lines = db.query(StockMovementLine).filter(StockMovementLine.movement_id == movement.id).all()
    for line in lines:
        item_obj = db.get(StockItem, line.item_id)
        if item_obj and not item_obj.is_stock_item:
            for comp in db.query(ItemBundle).filter(ItemBundle.bundle_item_id == line.item_id).all():
                db.add(StockMovementLine(
                    movement_id=movement.id,
                    item_id=comp.component_item_id,
                    qty=float(line.qty) * float(comp.qty),
                    uom_id=comp.uom_id,
                    from_location_id=line.from_location_id,
                    to_location_id=line.to_location_id,
                ))


def _net_qty(db: Session, item_id, exclude_id=None) -> float:
    q = db.query(func.sum(StockMovementLine.qty)).join(StockMovement).filter(
        StockMovementLine.item_id == item_id, StockMovement.status == "Posted",
    )
    if exclude_id:
        q = q.filter(StockMovement.id != exclude_id)
    return float(q.scalar() or 0)


def _last_avg_cost(db: Session, item_id) -> float:
    last = db.query(StockMovementLine).join(StockMovement).filter(
        StockMovementLine.item_id == item_id,
        StockMovement.move_type.in_(["receipt", "return"]),
        StockMovement.status == "Posted",
        StockMovementLine.running_avg_cost.isnot(None),
    ).order_by(StockMovement.created_at.desc()).first()
    return float(last.running_avg_cost) if last else 0.0


def _accounts_for_in(db: Session, item_obj, org_id: int):
    from .coa_resolver import CoaResolver
    stock = CoaResolver.resolve_stock_account(db, item_obj.id, org_id)
    # Use purchase/AP account as credit side for stock receipt
    ap = CoaResolver.resolve_ap_account(db, org_id)
    return stock, ap


def _accounts_for_out(db: Session, item_obj, org_id: int):
    from .coa_resolver import CoaResolver
    cogs = CoaResolver.resolve_cogs_account(db, item_obj.id, org_id)
    stock = CoaResolver.resolve_stock_account(db, item_obj.id, org_id)
    return cogs, stock


def _accounts_for_scrap(db: Session, item_obj, org_id: int):
    from .coa_resolver import CoaResolver
    variance = CoaResolver.resolve_variance_account(db, item_obj.id, org_id)
    stock = CoaResolver.resolve_stock_account(db, item_obj.id, org_id)
    return variance, stock
