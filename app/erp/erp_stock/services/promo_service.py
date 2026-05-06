from datetime import date
from decimal import Decimal
from app.erp.erp_stock.models.promo_bundle import StockPromoBundle, StockPromoBundleItem
from app.erp.erp_stock.services.price_service import get_price


def get_bundle_promo(cart_items: list, pricelist_id: int = None) -> dict:
    """
    Given a list of {product_id, qty} cart items and a pricelist_id,
    return {product_id: Decimal(price)} for products that match an active promo bundle.
    Only applies when ALL required items in a bundle are present in the cart.
    """
    if not cart_items:
        return {}

    today    = date.today()
    qty_map  = {int(i["product_id"]): Decimal(str(i["qty"])) for i in cart_items}
    cart_ids = set(qty_map.keys())

    q = StockPromoBundle.query.filter_by(is_active=True).filter(
        (StockPromoBundle.valid_from == None) | (StockPromoBundle.valid_from <= today),
        (StockPromoBundle.valid_to   == None) | (StockPromoBundle.valid_to   >= today),
    )
    if pricelist_id:
        q = q.filter(
            (StockPromoBundle.price_type_id == pricelist_id) |
            (StockPromoBundle.price_type_id == None)
        )

    result = {}
    for bundle in q.all():
        items = bundle.items
        if not items:
            continue
        required_ids = {item.product_id for item in items}
        if not required_ids.issubset(cart_ids):
            continue
        # All required products are in cart — check qty
        matched = all(qty_map.get(i.product_id, Decimal(0)) >= i.qty for i in items)
        if not matched:
            continue
        # Apply promo prices (highest specificity wins; don't overwrite already-set promo)
        for item in items:
            pid = item.product_id
            if pid in result:
                continue  # already won by another bundle
            if item.promo_price is not None:
                result[pid] = Decimal(str(item.promo_price))
            elif item.discount_pct is not None:
                base = get_price(pid, None, qty_map[pid], pricelist_id)
                result[pid] = base * (1 - Decimal(str(item.discount_pct)) / 100)

    return result
