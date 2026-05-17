from datetime import date
from sqlalchemy.orm import Session
from ..models import Item, PriceList

class PriceService:
    @staticmethod
    def get_price(db: Session, item_id: int, uom_id: int = None, qty: float = 1.0, pricelist_id: int = None) -> float:
        today = date.today()
        item = db.query(Item).filter_by(id=item_id).first()
        if not item:
            return 0.0

        query = db.query(PriceList).filter(
            (PriceList.valid_from == None) | (PriceList.valid_from <= today),
            (PriceList.valid_to == None) | (PriceList.valid_to >= today),
            PriceList.min_qty <= qty
        )

        if pricelist_id:
            query = query.filter(PriceList.price_type_id == pricelist_id)

        rule = query.filter(PriceList.item_id == item_id).order_by(PriceList.min_qty.desc()).first()

        if not rule and item.category_id:
            rule = query.filter(PriceList.item_id == None, PriceList.product_category_id == item.category_id).order_by(PriceList.min_qty.desc()).first()

        if not rule:
            rule = query.filter(PriceList.item_id == None, PriceList.product_category_id == None, PriceList.is_blanket == True).order_by(PriceList.min_qty.desc()).first()

        if rule and rule.price is not None:
            return rule.price

        return 0.0
