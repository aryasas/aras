from datetime import date
from sqlalchemy.orm import Session
from ..models import Product, PriceList

class PriceService:
    """Service for resolving product prices based on rules and pricelists."""
    
    @staticmethod
    def get_price(db: Session, product_id: int, uom_id: int = None, qty: float = 1.0, pricelist_id: int = None) -> float:
        """Resolve price for product+uom+qty with optional pricelist."""
        today = date.today()
        product = db.query(Product).filter_by(id=product_id).first()
        if not product:
            return 0.0
        
        # Base query for active price rules
        query = db.query(PriceList).filter(
            (PriceList.valid_from == None) | (PriceList.valid_from <= today),
            (PriceList.valid_to == None) | (PriceList.valid_to >= today),
            PriceList.min_qty <= qty
        )
        
        if pricelist_id:
            query = query.filter(PriceList.price_type_id == pricelist_id)
            
        # 1. Specific product match (highest priority)
        # Order by min_qty desc to get the most specific tier
        rule = query.filter(PriceList.product_id == product_id).order_by(PriceList.min_qty.desc()).first()
        
        if not rule and product.category_id:
            # 2. Category match
            rule = query.filter(PriceList.product_id == None, PriceList.product_category_id == product.category_id).order_by(PriceList.min_qty.desc()).first()
            
        if not rule:
            # 3. Blanket match
            rule = query.filter(PriceList.product_id == None, PriceList.product_category_id == None, PriceList.is_blanket == True).order_by(PriceList.min_qty.desc()).first()
            
        if rule:
            if rule.price is not None:
                return rule.price
            if rule.discount_pct is not None:
                return product.price * (1 - rule.discount_pct / 100)
                
        return product.price
