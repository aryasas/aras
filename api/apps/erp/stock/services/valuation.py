from sqlalchemy.orm import Session
from typing import Optional

from apps.erp.stock.models_valuation import StockLayer

class InventoryValuationService:
    @staticmethod
    def get_unit_cost(db: Session, product_id: int, org_id: int) -> float:
        """FIFO: return cost of oldest unconsumed stock layer."""
        layer = db.query(StockLayer).filter(
            StockLayer.product_id == product_id,
            StockLayer.org_id == org_id,
            StockLayer.qty_remaining > 0
        ).order_by(StockLayer.created_at).first() # FIFO
        
        if not layer:
            return 0.0 # Or raise an error if product is expected to have stock
        return layer.unit_cost

    @staticmethod
    def consume(db: Session, product_id: int, org_id: int, qty: float) -> float:
        """Consume qty units FIFO; return total cost consumed (for COGS)."""
        total_cost_consumed = 0.0
        remaining_qty_to_consume = qty

        layers = db.query(StockLayer).filter(
            StockLayer.product_id == product_id,
            StockLayer.org_id == org_id,
            StockLayer.qty_remaining > 0
        ).order_by(StockLayer.created_at).all() # FIFO

        for layer in layers:
            if remaining_qty_to_consume <= 0:
                break
            
            qty_from_layer = min(remaining_qty_to_consume, layer.qty_remaining)
            total_cost_consumed += qty_from_layer * layer.unit_cost
            layer.qty_remaining -= qty_from_layer
            remaining_qty_to_consume -= qty_from_layer
            db.add(layer)
        
        db.flush() # Ensure changes are committed before returning
        return total_cost_consumed

    @staticmethod
    def receive(db: Session, product_id: int, org_id: int, qty: float, unit_cost: float, source_ref: Optional[str] = None):
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
        db.flush() # Ensure the new layer is in the session
