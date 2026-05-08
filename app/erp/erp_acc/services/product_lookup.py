"""Product price + account lookup for invoice line entry."""
from decimal import Decimal
from arasCore.lib.core.action import action


@action(methods=["GET"], require_auth=True)
def product_price(product_id: int, qty: float = 1.0, price_type: str = "sales",
                  price_type_id: int = None, company_id: int = None,
                  uom_id: int = None):
    """Resolve unit price + uom + revenue/purchase account for a product.
    If uom_id is given, price is resolved for that UoM (so changing UoM
    on a line refetches the correct unit price).
    """
    from app.erp.erp_stock.models.product import StockProduct
    from app.erp.erp_stock.services.price import get_price
    from app.erp.erp_stock.services.coa_resolver import (
        resolve_revenue_account, resolve_purchase_account,
    )
    product = StockProduct.get(product_id)
    if not product:
        raise ValueError("Product not found")

    if not uom_id:
        if price_type == "sales":
            uom_id = product.uom_sales_id or product.uom_id
        else:
            uom_id = product.uom_purchase_id or product.uom_id

    price = get_price(product_id, uom_id, Decimal(str(qty)), price_type_id, price_type)

    acc_id = None
    if company_id:
        acc_id = (resolve_revenue_account(product, company_id) if price_type == "sales"
                  else resolve_purchase_account(product, company_id))

    return {
        "product_id":  product_id,
        "name":        product.name,
        "description": product.name,
        "uom_id":      uom_id,
        "unit_price":  float(price),
        "account_id":  acc_id,
    }
