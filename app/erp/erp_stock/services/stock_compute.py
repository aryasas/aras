"""
Compute stock qty and valuation directly from StockMovementLine.
Single source of truth — no stored qty_on_hand.
"""
from decimal import Decimal
from arasCore.lib.core.extensions import db
from sqlalchemy import func, case

IN_TYPES  = ("receipt", "opening", "adjustment", "return")
OUT_TYPES = ("delivery", "scrap")


def _get_company_avg_by_location(company_id: int) -> bool:
    if not company_id:
        return False
    from app.erp.erp_core.models.company import Company
    c = Company.get(company_id)
    return bool(c and c.avg_cost_by_location)


def compute_qty(product_id: int, location_id: int = None, company_id: int = None) -> Decimal:
    """
    SUM qty in - qty out from posted StockMovementLine.
    location_id=None → all locations (total qty for product).
    """
    from app.erp.erp_stock.models.movement import StockMovement, StockMovementLine

    base = (
        db.session.query(
            func.sum(
                case(
                    (StockMovement.dst_location_id == location_id if location_id else True,
                     case(
                         (StockMovement.move_type.in_(IN_TYPES), StockMovementLine.qty_base),
                         (StockMovement.move_type == "internal", StockMovementLine.qty_base),
                         else_=Decimal("0"),
                     )),
                    else_=Decimal("0"),
                )
            ) -
            func.sum(
                case(
                    (StockMovement.src_location_id == location_id if location_id else True,
                     case(
                         (StockMovement.move_type.in_(OUT_TYPES), StockMovementLine.qty_base),
                         (StockMovement.move_type == "internal", StockMovementLine.qty_base),
                         else_=Decimal("0"),
                     )),
                    else_=Decimal("0"),
                )
            )
        )
        .join(StockMovement, StockMovementLine.movement_id == StockMovement.id)
        .filter(
            StockMovementLine.product_id == product_id,
            StockMovement.state == "posted",
        )
    )

    if location_id:
        base = base.filter(
            db.or_(
                StockMovement.src_location_id == location_id,
                StockMovement.dst_location_id == location_id,
            )
        )
    if company_id:
        base = base.filter(StockMovement.company_id == company_id)

    result = base.scalar()
    return max(Decimal("0"), Decimal(str(result or 0)))


def compute_qty_by_location(product_id: int, company_id: int = None) -> dict:
    """
    Return {location_id: qty} for all locations that have posted movements.
    """
    from app.erp.erp_stock.models.movement import StockMovement, StockMovementLine

    q = (
        db.session.query(StockMovement.dst_location_id, StockMovement.src_location_id)
        .join(StockMovementLine, StockMovementLine.movement_id == StockMovement.id)
        .filter(
            StockMovementLine.product_id == product_id,
            StockMovement.state == "posted",
        )
    )
    if company_id:
        q = q.filter(StockMovement.company_id == company_id)

    loc_ids = set()
    for dst, src in q.all():
        if dst:
            loc_ids.add(dst)
        if src:
            loc_ids.add(src)

    return {
        loc_id: compute_qty(product_id, location_id=loc_id, company_id=company_id)
        for loc_id in loc_ids
    }


def compute_avg_cost(product_id: int, location_id: int = None, company_id: int = None) -> Decimal:
    """
    Return running_avg_cost from the most recent posted IN movement.
    If company.avg_cost_by_location=True and location_id given → filter by dst_location.
    Otherwise → any location (total avg).
    """
    from app.erp.erp_stock.models.movement import StockMovement, StockMovementLine

    by_location = _get_company_avg_by_location(company_id) if company_id else False

    q = (
        db.session.query(StockMovementLine.running_avg_cost)
        .join(StockMovement, StockMovementLine.movement_id == StockMovement.id)
        .filter(
            StockMovementLine.product_id == product_id,
            StockMovement.state == "posted",
            StockMovement.move_type.in_(IN_TYPES),
        )
        .order_by(StockMovement.date_move.desc(), StockMovement.id.desc())
    )

    if by_location and location_id:
        q = q.filter(StockMovement.dst_location_id == location_id)
    if company_id:
        q = q.filter(StockMovement.company_id == company_id)

    row = q.first()
    return Decimal(str(row[0] if row else 0))


def compute_total_value(product_id: int, location_id: int = None, company_id: int = None) -> Decimal:
    qty  = compute_qty(product_id, location_id=location_id, company_id=company_id)
    cost = compute_avg_cost(product_id, location_id=location_id, company_id=company_id)
    return qty * cost
