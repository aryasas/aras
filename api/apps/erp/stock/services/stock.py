from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import StockMovement, StockMovementLine, Location

class StockComputeService:
    """Service for stock quantities and valuation (WAC)."""

    @staticmethod
    def compute_qty(db: Session, product_id: int, location_id: int = None, sub_location_id: int = None) -> dict:
        in_filters = [
            StockMovementLine.product_id == product_id,
            StockMovement.status == "Posted",
        ]
        out_filters = [
            StockMovementLine.product_id == product_id,
            StockMovement.status == "Posted",
        ]

        if location_id:
            in_filters.append(StockMovement.to_location_id == location_id)
            out_filters.append(StockMovement.from_location_id == location_id)
        else:
            in_filters.append(StockMovement.to_location_id != None)
            out_filters.append(StockMovement.from_location_id != None)

        if sub_location_id:
            in_filters.append(StockMovementLine.to_location_id == sub_location_id)
            out_filters.append(StockMovementLine.from_location_id == sub_location_id)

        qty_in = db.query(func.sum(StockMovementLine.qty)).join(StockMovement).filter(*in_filters).scalar() or 0.0
        qty_out = db.query(func.sum(StockMovementLine.qty)).join(StockMovement).filter(*out_filters).scalar() or 0.0

        return {"value": qty_in - qty_out, "unit": "pcs"}

    @staticmethod
    def compute_qty_by_location(db: Session, product_id: int, parent_location_id: int) -> dict:
        locations = db.query(Location).filter(Location.parent_id == parent_location_id).all()
        return {
            loc.id: StockComputeService.compute_qty(db, product_id, location_id=parent_location_id, sub_location_id=loc.id)
            for loc in locations
        }

    @staticmethod
    def compute_avg_cost(db: Session, product_id: int) -> dict:
        """
        Calculate Weighted Average Cost.
        Formula: (Total Value of Inward Movements) / (Total Qty of Inward Movements)
        """
        result = db.query(
            func.sum(StockMovementLine.qty * StockMovementLine.unit_cost),
            func.sum(StockMovementLine.qty)
        ).join(StockMovement).filter(
            StockMovementLine.product_id == product_id,
            StockMovement.status == "Posted",
            StockMovement.move_type == "Incoming"
        ).first()
        
        total_value, total_qty = result or (0, 0)
        
        avg_cost = 0.0
        if total_qty and total_qty > 0:
            avg_cost = total_value / total_qty
        
        return {"value": avg_cost, "unit": "currency"}
