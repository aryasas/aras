from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from core import Aras
from ..models import StockMovement, StockMovementLine

class StockComputeService(Aras.Service):
    """Service for stock quantities and valuation."""
    model_class = StockMovement

    @classmethod
    def compute_qty(cls, db: Session, item_id: int, location_id: Optional[int] = None) -> float:
        from sqlalchemy import case as sa_case
        base = db.query(StockMovementLine).join(StockMovement).filter(
            StockMovementLine.item_id == item_id,
            StockMovement.status == "Posted",
            StockMovementLine.deleted_at.is_(None),
            StockMovement.deleted_at.is_(None),
        )
        if location_id:
            base = base.filter(
                (StockMovementLine.to_location_id == location_id) |
                (StockMovementLine.from_location_id == location_id)
            )
            signed = func.sum(sa_case(
                (StockMovementLine.to_location_id == location_id, StockMovementLine.qty),
                (StockMovementLine.from_location_id == location_id, -StockMovementLine.qty),
                else_=0.0
            ))
        else:
            # total: inflows minus outflows; internal transfers cancel automatically
            signed = func.sum(
                sa_case((StockMovementLine.to_location_id.isnot(None), StockMovementLine.qty), else_=0.0)
                - sa_case((StockMovementLine.from_location_id.isnot(None), StockMovementLine.qty), else_=0.0)
            )
        return float(base.with_entities(signed).scalar() or 0)

    @classmethod
    def compute_qty_by_location(cls, db: Session, item_id: int) -> list:
        from ..models import Location
        from sqlalchemy import union_all, select
        in_q = select(
            StockMovementLine.to_location_id.label("loc_id"),
            StockMovementLine.qty.label("qty")
        ).join(StockMovement).where(
            StockMovementLine.item_id == item_id,
            StockMovement.status == "Posted",
            StockMovementLine.deleted_at.is_(None),
            StockMovement.deleted_at.is_(None),
            StockMovementLine.to_location_id.isnot(None)
        )
        out_q = select(
            StockMovementLine.from_location_id.label("loc_id"),
            (-StockMovementLine.qty).label("qty")
        ).join(StockMovement).where(
            StockMovementLine.item_id == item_id,
            StockMovement.status == "Posted",
            StockMovementLine.deleted_at.is_(None),
            StockMovement.deleted_at.is_(None),
            StockMovementLine.from_location_id.isnot(None)
        )
        combined = union_all(in_q, out_q).subquery()
        rows = db.query(
            combined.c.loc_id,
            Location.name,
            func.sum(combined.c.qty).label("net_qty")
        ).join(Location, Location.id == combined.c.loc_id) \
         .group_by(combined.c.loc_id, Location.name) \
         .having(func.sum(combined.c.qty) != 0).all()
        return [{"location_id": r.loc_id, "location_name": r.name, "qty": float(r.net_qty)} for r in rows]

    @classmethod
    def compute_avg_cost(cls, db: Session, item_id: int) -> float:
        last = db.query(StockMovementLine).join(StockMovement).filter(
            StockMovementLine.item_id == item_id,
            StockMovement.move_type.in_(["receipt", "return"]),
            StockMovement.status == "Posted",
            StockMovementLine.deleted_at.is_(None),
            StockMovement.deleted_at.is_(None),
            StockMovementLine.running_avg_cost.isnot(None),
        ).order_by(StockMovement.created_at.desc()).first()
        return float(last.running_avg_cost) if last and last.running_avg_cost is not None else 0.0
