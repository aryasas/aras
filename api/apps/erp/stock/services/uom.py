from sqlalchemy.orm import Session
from ..models import ProductUom

class UomService:
    """Service for handling Unit of Measure conversions."""
    
    @staticmethod
    def convert_qty(db: Session, product_id: int, qty: float, from_uom_id: int, to_uom_id: int) -> float:
        """Convert quantity between UOMs using product-specific factors."""
        if from_uom_id == to_uom_id or from_uom_id is None or to_uom_id is None:
            return qty
        
        # Factors are relative to the product's base UOM (which has factor 1.0)
        # 1 Unit of UOM = factor * Base Units
        
        src = db.query(ProductUom).filter_by(product_id=product_id, uom_id=from_uom_id).first()
        dst = db.query(ProductUom).filter_by(product_id=product_id, uom_id=to_uom_id).first()
        
        from_factor = src.factor if src else 1.0
        to_factor = dst.factor if dst else 1.0
        
        if to_factor == 0:
            return qty
            
        return qty * from_factor / to_factor

    @staticmethod
    def get_factor(db: Session, product_id: int, uom_id: int) -> float:
        """Get the conversion factor for a specific product and UOM."""
        rec = db.query(ProductUom).filter_by(product_id=product_id, uom_id=uom_id).first()
        return rec.factor if rec else 1.0
