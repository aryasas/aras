from decimal import Decimal
from aras.app_erp.erp_stock.models.uom import StockUom
from aras.app_erp.erp_stock.models.product import StockProductUom


def convert_qty(product_id: int, qty: Decimal, from_uom_id: int, to_uom_id: int) -> Decimal:
    """Convert qty from from_uom to to_uom using product-specific or global ratio."""
    if from_uom_id == to_uom_id:
        return qty

    qty = Decimal(str(qty))

    # Try product-specific conversion first
    src = StockProductUom.query.filter_by(product_id=product_id, uom_id=from_uom_id).first()
    dst = StockProductUom.query.filter_by(product_id=product_id, uom_id=to_uom_id).first()

    from_uom = StockUom.query.get(from_uom_id)
    to_uom   = StockUom.query.get(to_uom_id)

    # Use product factor if available, else global ratio
    from_factor = Decimal(str(src.factor)) if src else (Decimal(str(from_uom.ratio)) if from_uom else Decimal("1"))
    to_factor   = Decimal(str(dst.factor)) if dst else (Decimal(str(to_uom.ratio))   if to_uom   else Decimal("1"))

    # Convert: qty_in_from × from_factor / to_factor
    if to_factor == 0:
        return qty
    return qty * from_factor / to_factor


def to_base_qty(product_id: int, qty: Decimal, uom_id: int, base_uom_id: int) -> Decimal:
    """Convert qty in given UoM to product's base UoM."""
    return convert_qty(product_id, qty, uom_id, base_uom_id)
