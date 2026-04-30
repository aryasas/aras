from datetime import date
from decimal import Decimal
from aras.erp.erp_stock.models.product import StockProduct, StockProductPrice


def get_price(product_id: int, uom_id: int, qty: Decimal,
              pricelist_id: int = None, price_type: str = "sales") -> Decimal:
    """
    Lookup price for product+uom+qty.
    Checks pricelist-linked rows first, then direct product price rows.
    """
    today   = date.today()
    qty     = Decimal(str(qty))
    product = StockProduct.get(product_id)
    if not product:
        return Decimal("0")

    base_q = (
        StockProductPrice.query
        .filter_by(product_id=product_id, is_active=True)
        .filter(StockProductPrice.min_qty <= qty)
        .filter(
            (StockProductPrice.valid_from == None) | (StockProductPrice.valid_from <= today)
        )
        .filter(
            (StockProductPrice.valid_to == None) | (StockProductPrice.valid_to >= today)
        )
    )

    if pricelist_id:
        item = (
            base_q
            .filter_by(price_list_id=pricelist_id)
            .order_by(StockProductPrice.min_qty.desc())
            .first()
        )
        if item:
            return Decimal(str(item.price))

    if product.use_price_table:
        pp = (
            base_q
            .filter_by(price_type=price_type, price_list_id=None)
            .filter((StockProductPrice.uom_id == uom_id) | (StockProductPrice.uom_id == None))
            .order_by(StockProductPrice.uom_id.desc(), StockProductPrice.min_qty.desc())
            .first()
        )
        if pp:
            return Decimal(str(pp.price))

    return Decimal("0")
