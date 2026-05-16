from sqlalchemy.orm import Session
from sqlalchemy import func, asc, desc

from ..models_valuation import StockLayer

class InventoryValuationService:
    @staticmethod
    def get_unit_cost(db: Session, product_id: int, org_id: int) -> float:
        """FIFO: return cost of oldest unconsumed stock layer."""
        oldest_layer = db.query(StockLayer).filter(
            StockLayer.product_id == product_id,
            StockLayer.org_id == org_id,
            StockLayer.qty_remaining > 0
        ).order_by(asc(StockLayer.created_at)).first() # Assuming 'created_at' for age
        
        if oldest_layer:
            return oldest_layer.unit_cost
        return 0.0 # No stock available

    @staticmethod
    def consume(db: Session, product_id: int, org_id: int, qty: float) -> float:
        """Consume qty units FIFO; return total cost consumed (for COGS)."""
        total_cost_consumed = 0.0
        qty_to_consume = qty

        while qty_to_consume > 0:
            oldest_layer = db.query(StockLayer).filter(
                StockLayer.product_id == product_id,
                StockLayer.org_id == org_id,
                StockLayer.qty_remaining > 0
            ).order_by(asc(StockLayer.created_at)).first()

            if not oldest_layer:
                # Ran out of stock before consuming all qty_to_consume
                # This could indicate a negative stock scenario if not handled upstream
                break 

            can_consume_from_layer = min(qty_to_consume, oldest_layer.qty_remaining)
            total_cost_consumed += can_consume_from_layer * oldest_layer.unit_cost
            qty_to_consume -= can_consume_from_layer
            oldest_layer.qty_remaining -= can_consume_from_layer
            db.add(oldest_layer)
        
        db.flush() # Flush to ensure changes are reflected for subsequent operations if needed
        return total_cost_consumed

    @staticmethod
    def receive(db: Session, product_id: int, org_id: int, qty: float, unit_cost: float, source_ref: str = None):
        """Add a new stock layer on goods receipt."""
        new_layer = StockLayer(
            product_id=product_id,
            org_id=org_id,
            qty_received=qty,
            qty_remaining=qty,
            unit_cost=unit_cost,
            source_ref=source_ref
        )
        db.add(new_layer)
        db.flush() # Flush to ensure the layer is added for immediate consumption if needed
