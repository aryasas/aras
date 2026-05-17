from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import StockMovement, StockMovementLine, Location
from decimal import Decimal

class StockComputeService:
    """Service for stock quantities and valuation."""

    @staticmethod
    def compute_qty(db: Session, item_id: int, location_id: int = None) -> float:
        q = db.query(func.sum(StockMovementLine.qty)).join(StockMovement).filter(
            StockMovementLine.item_id == item_id,
            StockMovement.status == "Posted",
        )
        if location_id:
            q = q.filter(StockMovementLine.to_location_id == location_id)
        return float(q.scalar() or 0)

    @staticmethod
    def compute_qty_by_location(db: Session, item_id: int) -> dict:
        rows = db.query(
            StockMovementLine.to_location_id,
            func.sum(StockMovementLine.qty)
        ).join(StockMovement).filter(
            StockMovementLine.item_id == item_id,
            StockMovement.status == "Posted",
        ).group_by(StockMovementLine.to_location_id).all()
        return {loc_id: float(qty) for loc_id, qty in rows}

    @staticmethod
    def compute_avg_cost(db: Session, item_id: int) -> float:
        last = db.query(StockMovementLine).join(StockMovement).filter(
            StockMovementLine.item_id == item_id,
            StockMovement.move_type.in_(["receipt", "return"]),
            StockMovement.status == "Posted",
            StockMovementLine.running_avg_cost.isnot(None),
        ).order_by(StockMovement.created_at.desc()).first()
        return float(last.running_avg_cost) if last else 0.0
