from datetime import date
from decimal import Decimal
from aras.app_erp.erp_stock.models.pricelist import StockPriceListItem
from aras.app_erp.erp_stock.models.product import StockProduct


def get_price(product_id: int, uom_id: int, qty: Decimal,
              pricelist_id: int = None) -> Decimal:
    """
    Lookup selling price for product+uom+qty.
    1. If pricelist_id given: check StockPriceListItem
    2. Fallback: StockProductPrice (sales, matching uom or no uom)
    3. Fallback: product.standard_price
    """
    today = date.today()
    qty = Decimal(str(qty))

    if pricelist_id:
        item = (
            StockPriceListItem.query
            .filter_by(price_list_id=pricelist_id, product_id=product_id, uom_id=uom_id)
            .filter(StockPriceListItem.min_qty <= qty)
            .filter(
                (StockPriceListItem.valid_from == None) | (StockPriceListItem.valid_from <= today)
            )
            .filter(
                (StockPriceListItem.valid_to == None) | (StockPriceListItem.valid_to >= today)
            )
            .order_by(StockPriceListItem.min_qty.desc())
            .first()
        )
        if item:
            return Decimal(str(item.price))

    # Fallback: StockProductPrice
    from aras.app_erp.erp_stock.models.product import StockProductPrice
    pp = (
        StockProductPrice.query
        .filter_by(product_id=product_id, price_type="sales")
        .filter(
            (StockProductPrice.uom_id == uom_id) | (StockProductPrice.uom_id == None)
        )
        .filter(StockProductPrice.min_qty <= qty)
        .filter(StockProductPrice.is_active == True)
        .order_by(StockProductPrice.uom_id.desc(), StockProductPrice.min_qty.desc())
        .first()
    )
    if pp:
        return Decimal(str(pp.price))

    product = StockProduct.query.get(product_id)
    return Decimal(str(product.standard_price)) if product else Decimal("0")
