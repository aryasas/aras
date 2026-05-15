from sqlalchemy.orm import Session
from sqlalchemy import func, case
from ..models import StockMovement, StockMovementLine, Product

class StockService:
    """Service for stock quantities and valuation (WAC)."""
    
    @staticmethod
    def get_qty(db: Session, product_id: int, warehouse_id: int = None) -> float:
        """Calculate current quantity on hand."""
        # Qty In (where to_warehouse_id matches)
        qty_in = db.query(func.sum(StockMovementLine.qty)).join(StockMovement).filter(
            StockMovementLine.product_id == product_id,
            StockMovement.status == "Posted",
            StockMovement.to_warehouse_id == warehouse_id if warehouse_id else StockMovement.to_warehouse_id != None
        ).scalar() or 0.0
        
        # Qty Out (where from_warehouse_id matches)
        qty_out = db.query(func.sum(StockMovementLine.qty)).join(StockMovement).filter(
            StockMovementLine.product_id == product_id,
            StockMovement.status == "Posted",
            StockMovement.from_warehouse_id == warehouse_id if warehouse_id else StockMovement.from_warehouse_id != None
        ).scalar() or 0.0
        
        return qty_in - qty_out

    @staticmethod
    def get_wac(db: Session, product_id: int) -> float:
        """
        Calculate Weighted Average Cost.
        Formula: (Total Value of Inward Movements) / (Total Qty of Inward Movements)
        Note: Simplified version. A production system would use a running WAC snapshot.
        """
        result = db.query(
            func.sum(StockMovementLine.qty * StockMovementLine.amount),
            func.sum(StockMovementLine.qty)
        ).join(StockMovement).filter(
            StockMovementLine.product_id == product_id,
            StockMovement.status == "Posted",
            StockMovement.to_warehouse_id != None # Only inward movements for cost base
        ).first()
        
        total_value, total_qty = result
        if total_qty and total_qty > 0:
            return total_value / total_qty
        
        # Fallback to product base price if no movements
        product = db.query(Product).get(product_id)
        return getattr(product, "base_cost", 0.0)
