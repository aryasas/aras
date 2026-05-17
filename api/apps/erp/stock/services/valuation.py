from sqlalchemy.orm import Session
from typing import Optional

from apps.erp.stock.models import StockMovementLine
from apps.erp.config.models import Organization


def _get_valuation_method(db: Session, org_id: int) -> str:
    org = db.get(Organization, org_id)
    return (org.stock_valuation_method if org else None) or "FIFO"


class InventoryValuationService:
    @staticmethod
    def get_unit_cost(db: Session, item_id: int, org_id: int) -> float:
        method = _get_valuation_method(db, org_id)
        if method == "AVERAGE":
            line = db.query(StockMovementLine).filter(
                StockMovementLine.item_id == item_id,
                StockMovementLine.qty_remaining > 0,
            ).order_by(StockMovementLine.created_at.desc()).first()
            return float(line.running_avg_cost or line.unit_cost) if line else 0.0
        # FIFO default
        line = db.query(StockMovementLine).filter(
            StockMovementLine.item_id == item_id,
            StockMovementLine.qty_remaining > 0,
        ).order_by(StockMovementLine.created_at).first()
        return float(line.unit_cost) if line else 0.0

    @staticmethod
    def consume(db: Session, item_id: int, org_id: int, qty: float) -> float:
        """Consume qty units per company valuation method; return total cost consumed (COGS)."""
        method = _get_valuation_method(db, org_id)
        total_cost = 0.0
        remaining = qty

        if method == "AVERAGE":
            lines = db.query(StockMovementLine).filter(
                StockMovementLine.item_id == item_id,
                StockMovementLine.qty_remaining > 0,
            ).order_by(StockMovementLine.created_at.desc()).all()
        else:
            lines = db.query(StockMovementLine).filter(
                StockMovementLine.item_id == item_id,
                StockMovementLine.qty_remaining > 0,
            ).order_by(StockMovementLine.created_at).all()

        for line in lines:
            if remaining <= 0:
                break
            taken = min(remaining, line.qty_remaining)
            cost_per_unit = float(line.running_avg_cost or line.unit_cost)
            total_cost += taken * cost_per_unit
            line.qty_remaining -= taken
            remaining -= taken

        db.flush()
        return total_cost

    @staticmethod
    def receive(db: Session, item_id: int, org_id: int, qty: float, unit_cost: float, source_line_id: int):
        """Mark the receipt StockMovementLine as a FIFO/AVERAGE layer by setting qty_remaining."""
        line = db.get(StockMovementLine, source_line_id)
        if line:
            line.qty_remaining = qty
            db.flush()
