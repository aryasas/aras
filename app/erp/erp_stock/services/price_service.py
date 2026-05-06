from datetime import date
from decimal import Decimal
from app.erp.erp_stock.models.product import StockProduct, StockPriceList

SPP = StockPriceList


def get_price(product_id: int, uom_id: int, qty: Decimal,
              pricelist_id: int = None, price_type: str = "sales",
              location_id: int = None, terminal_id: int = None) -> Decimal:
    """
    Resolve price for product+uom+qty with optional pricelist and store scope.
    Resolution order (highest → lowest specificity):
      1. item-level (product_id match within pricelist)
      2. terminal + category
      3. terminal + blanket
      4. location + category
      5. location + blanket
      6. category only
      7. blanket only
      8. standalone product price (no pricelist)
    discount_pct rows are applied against the standalone base price.
    """
    today = date.today()
    qty   = Decimal(str(qty))

    product = StockProduct.get(product_id)
    if not product:
        return Decimal("0")
    category_id = product.category_id

    def _base_q():
        return (
            SPP.query
            .filter_by(is_active=True)
            .filter(SPP.min_qty <= qty)
            .filter((SPP.valid_from == None) | (SPP.valid_from <= today))
            .filter((SPP.valid_to   == None) | (SPP.valid_to   >= today))
        )

    def _to_price(row) -> Decimal:
        if row.discount_pct is not None and (not row.price or row.price == 0):
            base = _standalone_price(product_id, uom_id, qty, price_type)
            return base * (1 - Decimal(str(row.discount_pct)) / 100)
        return Decimal(str(row.price))

    def _standalone_price(pid, uid, q, pt) -> Decimal:
        pp = (
            _base_q()
            .filter_by(product_id=pid, price_type=pt, price_type_id=None)
            .filter((SPP.uom_id == uid) | (SPP.uom_id == None))
            .order_by(SPP.uom_id.desc(), SPP.min_qty.desc())
            .first()
        )
        return Decimal(str(pp.price)) if pp else Decimal("0")

    if pricelist_id:
        # Try with price_type filter first, fall back to any price_type in pricelist
        def _pricelist_lookup(pt_filter):
            q = _base_q().filter_by(price_type_id=pricelist_id)
            if pt_filter:
                q = q.filter_by(price_type=pt_filter)

            # 1. item-level
            row = q.filter_by(product_id=product_id).order_by(SPP.min_qty.desc()).first()
            if row:
                return _to_price(row)

            # 2-3. terminal-scoped
            if terminal_id:
                row = (q.filter_by(terminal_id=terminal_id, product_id=None)
                        .filter(
                            (SPP.product_category_id == category_id) | (SPP.is_blanket == True)
                        )
                        .order_by(SPP.product_category_id.desc(), SPP.min_qty.desc())
                        .first())
                if row:
                    return _to_price(row)

            # 4-5. location-scoped
            if location_id:
                row = (q.filter_by(location_id=location_id, product_id=None)
                        .filter(
                            (SPP.product_category_id == category_id) | (SPP.is_blanket == True)
                        )
                        .order_by(SPP.product_category_id.desc(), SPP.min_qty.desc())
                        .first())
                if row:
                    return _to_price(row)

            # 6. category only
            if category_id:
                row = (q.filter_by(product_id=None, product_category_id=category_id,
                                    terminal_id=None, location_id=None)
                        .order_by(SPP.min_qty.desc()).first())
                if row:
                    return _to_price(row)

            # 7. blanket
            row = (q.filter_by(is_blanket=True, product_id=None, product_category_id=None,
                                terminal_id=None, location_id=None)
                    .order_by(SPP.min_qty.desc()).first())
            return _to_price(row) if row else None

        result = _pricelist_lookup(price_type)
        if result is None:
            result = _pricelist_lookup(None)
        if result is not None:
            return result

    # 8. standalone (no pricelist)
    pp = _standalone_price(product_id, uom_id, qty, price_type)
    return pp
