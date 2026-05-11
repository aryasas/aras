from decimal import Decimal
from app.erp.erp_stock.models.uom import StockUom
from app.erp.erp_stock.models.product import StockProductUom


def convert_qty(product_id: int, qty: Decimal, from_uom_id: int, to_uom_id: int) -> Decimal:
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

    if not from_uom:
        raise ValueError(f"From UOM with ID {from_uom_id} not found.")
    if not to_uom:
        raise ValueError(f"To UOM with ID {to_uom_id} not found.")

    from_factor = Decimal(str(src.factor)) if src else Decimal("1")
    to_factor   = Decimal(str(dst.factor)) if dst else Decimal("1")

    return qty if to_factor == 0 else qty * from_factor / to_factor

def to_base_qty(product_id: int, qty: Decimal, uom_id: int, base_uom_id: int) -> Decimal:
    """Convert qty in given UoM to product's base UoM."""
    return convert_qty(product_id, qty, uom_id, base_uom_id)

def get_factor(product_id: int, uom_id: int, base_uom_id: int) -> Decimal:
    """Return how many base-UOM units equal 1 unit of uom_id (factor for price conversion)."""
    if uom_id == base_uom_id:
        return Decimal("1")
    rec = StockProductUom.find(product_id=product_id, uom_id=uom_id)
    return Decimal(str(rec.factor)) if rec else Decimal("1")
