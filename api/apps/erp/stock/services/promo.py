from datetime import date
from sqlalchemy.orm import Session
from ..models import PromoBundle, PromoBundleItem
from .price import PriceService

class PromoService:
    """Service for calculating bundle promotions."""
    
    @staticmethod
    def get_bundle_discounts(db: Session, items: list[dict], pricelist_id: int = None) -> dict[int, float]:
        """
        Check cart items for active promo bundles and return adjusted prices.
        items format: [{'item_id': int, 'qty': float}]
        """
        if not items:
            return {}

        today = date.today()
        qty_map = {int(i["item_id"]): float(i["qty"]) for i in items}
        product_ids = set(qty_map.keys())

        # Find active bundles
        bundles = db.query(PromoBundle).filter(
            PromoBundle.is_active == True,
            (PromoBundle.valid_from == None) | (PromoBundle.valid_from <= today),
            (PromoBundle.valid_to == None) | (PromoBundle.valid_to >= today)
        )
        
        if pricelist_id:
            bundles = bundles.filter(
                (PromoBundle.price_type_id == pricelist_id) | (PromoBundle.price_type_id == None)
            )

        promo_prices = {}
        for bundle in bundles:
            # Check if all items in bundle are in the cart with sufficient qty
            bundle_items = db.query(PromoBundleItem).filter_by(bundle_id=bundle.id).all()
            if not bundle_items:
                continue
                
            match = True
            for bi in bundle_items:
                if bi.item_id not in product_ids or qty_map[bi.item_id] < bi.qty:
                    match = False
                    break
            
            if match:
                # Apply bundle pricing
                for bi in bundle_items:
                    pid = bi.item_id
                    if pid in promo_prices:
                        continue # Already covered by another bundle
                        
                    if bi.promo_price is not None:
                        promo_prices[pid] = bi.promo_price
                    elif bi.discount_pct is not None:
                        base_price = PriceService.get_price(db, pid, qty=qty_map[pid], pricelist_id=pricelist_id)
                        promo_prices[pid] = base_price * (1 - bi.discount_pct / 100)
                        
        return promo_prices
