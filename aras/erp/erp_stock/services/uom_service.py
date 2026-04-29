from decimal import Decimal
from aras.erp.erp_stock.models.uom import StockUom
from aras.erp.erp_stock.models.product import StockProductUom


def convert_qty(product_id: int, qty: Decimal, from_uom_id: int, to_uom_id: int) -> Decimal:
    print(f"DEBUG: convert_qty called with from_uom_id={from_uom_id}, to_uom_id={to_uom_id}")
    """Convert qty from from_uom to to_uom using product-specific or global ratio."""
    if from_uom_id is None:
        raise ValueError("from_uom_id cannot be None for UOM conversion.")
    if from_uom_id == to_uom_id:
        return qty

    qty      = Decimal(str(qty))
    src      = StockProductUom.find(product_id=product_id, uom_id=from_uom_id)
    dst      = StockProductUom.find(product_id=product_id, uom_id=to_uom_id)
    from_uom = StockUom.get(from_uom_id)
    to_uom   = StockUom.get(to_uom_id)

    print(f"DEBUG: Type of from_uom: {type(from_uom)}, Value: {from_uom}")
    print(f"DEBUG: Type of to_uom: {type(to_uom)}, Value: {to_uom}")

    if not from_uom:
        raise ValueError(f"From UOM with ID {from_uom_id} not found.")
    if not to_uom:
        raise ValueError(f"To UOM with ID {to_uom_id} not found.")

    from_factor = Decimal(str(src.factor)) if src else (Decimal(str(from_uom.ratio)) if from_uom else Decimal("1"))
    to_factor   = Decimal(str(dst.factor)) if dst else (Decimal(str(to_uom.ratio))   if to_uom   else Decimal("1"))

    return qty if to_factor == 0 else qty * from_factor / to_factor

def to_base_qty(product_id: int, qty: Decimal, uom_id: int, base_uom_id: int) -> Decimal:
    """Convert qty in given UoM to product's base UoM."""
    return convert_qty(product_id, qty, uom_id, base_uom_id)
