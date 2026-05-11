# Bugfix Requirements Document

## Introduction

When posting a Purchase Invoice, `post_purchase_invoice` in `purchase_posting.py` auto-creates a
`StockMovement` receipt with one `StockMovementLine` per product. The `qty_base` field on each line
is supposed to hold the quantity expressed in the product's base (stock) UOM, but it is instead
copied verbatim from `qty` (the purchase UOM quantity). This means inventory valuation and stock
ledger quantities are wrong whenever the purchase UOM differs from the base UOM (e.g. buying in
"box" when the base UOM is "pcs"). Additionally, `total_cost` is computed from `qty` instead of
`qty_base`, causing incorrect inventory cost entries.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a Purchase Invoice line has a UOM that differs from the product's base UOM THEN the system
    sets `StockMovementLine.qty_base` equal to `qty` (the purchase quantity) instead of converting
    it to the base UOM quantity.

1.2 WHEN a Purchase Invoice line has a UOM that differs from the product's base UOM THEN the system
    computes `StockMovementLine.total_cost` as `qty * unit_cost` (purchase quantity × cost) instead
    of `qty_base * unit_cost` (base quantity × cost), producing an incorrect inventory valuation.

1.3 WHEN the purchase UOM is the same as the product's base UOM THEN the system sets `qty_base`
    equal to `qty`, which happens to be numerically correct but is achieved without calling the
    conversion function.

### Expected Behavior (Correct)

2.1 WHEN a Purchase Invoice line has a UOM that differs from the product's base UOM THEN the system
    SHALL compute `StockMovementLine.qty_base` by calling
    `convert_qty(product_id, qty, from_uom_id=line.uom_id, to_uom_id=product.uom_id)` from
    `uom_service.py`, yielding the quantity in the product's base UOM.

2.2 WHEN a Purchase Invoice line has a UOM that differs from the product's base UOM THEN the system
    SHALL compute `StockMovementLine.total_cost` as `qty_base * unit_cost` (base quantity × cost)
    so that inventory valuation reflects the correct base-UOM quantity.

2.3 WHEN the purchase UOM is the same as the product's base UOM THEN the system SHALL still call
    `convert_qty()` (which returns `qty` unchanged when `from_uom_id == to_uom_id`), ensuring a
    single consistent code path for all cases.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a Purchase Invoice line has no explicit UOM set (`line.uom_id` is None) and the fallback
    resolves to the product's base UOM THEN the system SHALL CONTINUE TO produce
    `qty_base == qty` on the movement line (no conversion needed).

3.2 WHEN a Purchase Invoice is posted for a product that is not a stock item
    (`product.is_stock_item` is False) THEN the system SHALL CONTINUE TO skip stock movement
    line creation for that product.

3.3 WHEN a Purchase Invoice is posted THEN the system SHALL CONTINUE TO create the journal entry
    (DR inventory / CR payable) using the invoice line subtotals, unaffected by the UOM conversion
    change.

3.4 WHEN a Purchase Invoice is posted THEN the system SHALL CONTINUE TO call `post_movement()` on
    the resulting `StockMovement`, triggering downstream valuation updates as before.

3.5 WHEN a Purchase Invoice line's purchase UOM equals the product's base UOM THEN the system
    SHALL CONTINUE TO record `qty_base == qty` on the movement line (conversion factor of 1).

---

## Bug Condition (Pseudocode)

```pascal
FUNCTION isBugCondition(line, product)
  INPUT: line of type AccPurchaseInvoiceLine, product of type StockProduct
  OUTPUT: boolean

  effective_uom_id ← line.uom_id IF line.uom_id IS NOT NULL ELSE product.uom_id
  RETURN effective_uom_id ≠ product.uom_id
END FUNCTION
```

### Fix Checking Property

```pascal
// Property: Fix Checking — qty_base must reflect base-UOM quantity
FOR ALL (line, product) WHERE isBugCondition(line, product) DO
  movement_line ← post_purchase_invoice'(line, product)
  expected_base ← convert_qty(product.id, line.qty,
                               from_uom_id=line.uom_id,
                               to_uom_id=product.uom_id)
  ASSERT movement_line.qty_base = expected_base
  ASSERT movement_line.total_cost = expected_base * line.unit_price
END FOR
```

### Preservation Checking Property

```pascal
// Property: Preservation — non-buggy inputs (same UOM) must be unaffected
FOR ALL (line, product) WHERE NOT isBugCondition(line, product) DO
  ASSERT post_purchase_invoice(line, product).qty_base
       = post_purchase_invoice'(line, product).qty_base
END FOR
```
