from datetime import date
from decimal import Decimal
from aras.erp.erp_stock.models.pricelist import StockPriceListItem
from aras.erp.erp_stock.models.product import StockProduct, StockProductPrice


def get_price(product_id: int, uom_id: int, qty: Decimal,
              pricelist_id: int = None, price_type: str = "sales") -> Decimal:
    """
    Lookup price for product+uom+qty.
    Checks pricelist first, then StockProductPrice table.
    Returns 0 if no price found.
    """
    today   = date.today()
    qty     = Decimal(str(qty))
    product = StockProduct.get(product_id)
    if not product:
        return Decimal("0")

    if pricelist_id:
        q = (StockPriceListItem.query
             .filter_by(price_list_id=pricelist_id, product_id=product_id)
             .filter(StockPriceListItem.min_qty <= qty))
        if hasattr(StockPriceListItem, "valid_from"):
            q = q.filter(
                (StockPriceListItem.valid_from == None) | (StockPriceListItem.valid_from <= today)
            ).filter(
                (StockPriceListItem.valid_to == None) | (StockPriceListItem.valid_to >= today)
            )
        item = q.order_by(StockPriceListItem.min_qty.desc()).first()
        if item:
            return Decimal(str(item.price))

    if product.use_price_table:
        pp = (
            StockProductPrice.query
            .filter_by(product_id=product_id, price_type=price_type, is_active=True)
            .filter((StockProductPrice.uom_id == uom_id) | (StockProductPrice.uom_id == None))
            .filter(StockProductPrice.min_qty <= qty)
            .order_by(StockProductPrice.uom_id.desc(), StockProductPrice.min_qty.desc())
            .first()
        )
        if pp:
            return Decimal(str(pp.price))

    return Decimal("0")
