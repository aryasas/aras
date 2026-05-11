# Purchase UOM Stock Conversion Bugfix Design

## Overview

When `post_purchase_invoice()` builds `StockMovementLine` objects, it copies `qty` directly into
`qty_base` and computes `total_cost` as `qty * unit_cost`. This is wrong whenever the purchase UOM
differs from the product's base (stock) UOM — for example, buying in "box" when the base UOM is
"pcs". The fix is minimal: call `convert_qty()` from `uom_service.py` to derive `qty_base`, then
compute `total_cost` as `qty_base * unit_cost`. No other logic in the function changes.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — the effective purchase UOM on an
  invoice line differs from the product's base UOM (`line.uom_id ≠ product.uom_id`).
- **Property (P)**: The desired behavior when the bug condition holds — `qty_base` must equal the
  result of `convert_qty(product_id, qty, from_uom_id, to_uom_id)` and `total_cost` must equal
  `qty_base * unit_cost`.
- **Preservation**: Existing behavior for lines where the purchase UOM equals the base UOM, for
  non-stock products, and for journal entry creation — all must remain unchanged.
- **`post_purchase_invoice()`**: The function in
  `aras/erp/erp_acc/services/purchase_posting.py` that posts a purchase invoice, creates a journal
  entry, and creates a `StockMovement` receipt with `StockMovementLine` rows.
- **`convert_qty()`**: The function in `aras/erp/erp_stock/services/uom_service.py` that converts
  a quantity from one UOM to another using product-specific or global conversion factors. Returns
  `qty` unchanged when `from_uom_id == to_uom_id`.
- **`qty_base`**: The `StockMovementLine` field that stores quantity in the product's base (stock)
  UOM. Used by `post_movement()` for WAC computation and journal amounts.
- **`total_cost`**: The `StockMovementLine` field that stores `qty_base * unit_cost`. Used by
  `post_movement()` for inventory valuation journal entries.
- **base UOM**: The UOM stored on `StockProduct.uom_id` — the canonical unit for stock ledger
  quantities.
- **purchase UOM**: The UOM on the invoice line (`line.uom_id`), which may differ from the base
  UOM (e.g. "box" vs "pcs").

## Bug Details

### Bug Condition

The bug manifests when a `StockMovementLine` is created inside `post_purchase_invoice()` for a
product whose effective purchase UOM differs from its base UOM. The function assigns
`qty_base = sl["qty"]` (the raw purchase quantity) instead of converting it, and computes
`total_cost = sl["qty"] * sl["unit_cost"]` instead of using the converted base quantity.

**Formal Specification:**
```
FUNCTION isBugCondition(line, product)
  INPUT: line of type AccPurchaseInvoiceLine, product of type StockProduct
  OUTPUT: boolean

  effective_uom_id ← line.uom_id IF line.uom_id IS NOT NULL ELSE product.uom_id
  RETURN effective_uom_id ≠ product.uom_id
END FUNCTION
```

### Examples

- **Buying 10 boxes, 1 box = 12 pcs**: `qty = 10`, `qty_base` should be `120` but is stored as
  `10`. `total_cost` should be `120 * unit_cost` but is `10 * unit_cost` — inventory is
  undervalued by 12×.
- **Buying 5 cartons, 1 carton = 6 pcs**: `qty = 5`, `qty_base` should be `30` but is stored as
  `5`. WAC computation in `post_movement()` uses the wrong base quantity, corrupting the running
  average cost.
- **Buying 3 kg, base UOM is also kg**: `qty = 3`, `qty_base = 3` — numerically correct, but
  achieved without calling `convert_qty()`, so the code path is inconsistent.
- **Edge case — `line.uom_id` is None, fallback to `product.uom_id`**: effective UOM equals base
  UOM, so `isBugCondition` returns false; `qty_base` should equal `qty` and does.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Journal entry creation (DR inventory / CR payable) uses invoice line `subtotal` values and must
  not be affected by the UOM conversion change.
- Products with `is_stock_item = False` continue to be skipped for stock movement line creation.
- `post_movement()` is still called on the resulting `StockMovement` with `skip_journal=True`,
  triggering downstream WAC and state updates as before.
- When `line.uom_id` is None, the fallback to `product.uom_id` continues to produce
  `qty_base == qty` (same UOM, factor = 1).
- When the purchase UOM equals the base UOM, `qty_base == qty` is preserved (conversion returns
  the input unchanged).

**Scope:**
All inputs where `isBugCondition` returns false — same-UOM lines, non-stock products, journal
logic, and `post_movement()` invocation — must be completely unaffected by this fix.

## Hypothesized Root Cause

Based on reading the code, the cause is straightforward:

1. **Hardcoded copy instead of conversion**: In the `StockMovementLine` construction loop,
   `qty_base=sl["qty"]` was written as a shortcut with the comment `# same as qty (base UOM
   purchase)`. This assumption is only valid when the purchase UOM equals the base UOM.

2. **`total_cost` derived from wrong quantity**: `total_cost=sl["qty"] * sl["unit_cost"]` follows
   from the same incorrect assumption. Once `qty_base` is correct, `total_cost` must use it.

3. **No import of `convert_qty`**: `uom_service` is not imported in `purchase_posting.py`, so the
   conversion function was never wired in. The fix requires adding the import.

4. **`product.uom_id` not passed through to stock line dict**: The `stock_lines` list only stores
   `product_id`, `uom_id` (purchase UOM), `qty`, and `unit_cost`. The product's base `uom_id`
   must also be available at construction time to call `convert_qty()`.

## Correctness Properties

Property 1: Bug Condition — qty_base and total_cost reflect base-UOM quantity

_For any_ invoice line where the bug condition holds (`isBugCondition(line, product)` returns
true), the fixed `post_purchase_invoice()` SHALL produce a `StockMovementLine` where:
- `qty_base` equals `convert_qty(product_id, qty, from_uom_id=effective_uom_id, to_uom_id=product.uom_id)`
- `total_cost` equals `qty_base * unit_cost`

**Validates: Requirements 2.1, 2.2**

Property 2: Preservation — same-UOM lines are unaffected

_For any_ invoice line where the bug condition does NOT hold (`isBugCondition` returns false —
i.e. the effective purchase UOM equals the product's base UOM), the fixed
`post_purchase_invoice()` SHALL produce a `StockMovementLine` with the same `qty_base` and
`total_cost` as the original function, preserving stock ledger correctness for same-UOM purchases.

**Validates: Requirements 3.1, 3.5**

## Fix Implementation

### Changes Required

**File**: `aras/erp/erp_acc/services/purchase_posting.py`

**Function**: `post_purchase_invoice()`

**Specific Changes**:

1. **Add import**: Import `convert_qty` from `uom_service` at the top of the file:
   ```python
   from aras.erp.erp_stock.services.uom_service import convert_qty
   ```

2. **Pass base UOM into stock line dict**: When appending to `stock_lines`, include the product's
   base UOM so it is available during `StockMovementLine` construction:
   ```python
   stock_lines.append({
       "product_id": line.product_id,
       "uom_id":     uom_id,
       "base_uom_id": product.uom_id,   # ← add this
       "qty":        qty,
       "unit_cost":  price,
   })
   ```

3. **Compute `qty_base` via `convert_qty()`**: Replace the hardcoded copy with a conversion call:
   ```python
   qty_base = convert_qty(
       sl["product_id"], sl["qty"],
       from_uom_id=sl["uom_id"],
       to_uom_id=sl["base_uom_id"],
   )
   ```

4. **Compute `total_cost` from `qty_base`**: Replace `sl["qty"] * sl["unit_cost"]` with:
   ```python
   total_cost = qty_base * sl["unit_cost"]
   ```

5. **Update `StockMovementLine` construction**:
   ```python
   db.session.add(StockMovementLine(
       movement_id=mv.id,
       product_id=sl["product_id"],
       uom_id=sl["uom_id"],
       qty=sl["qty"],
       qty_base=qty_base,
       unit_cost=sl["unit_cost"],
       total_cost=total_cost,
   ))
   ```

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate
the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or
refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Create a purchase invoice line with a purchase UOM that differs from the product's
base UOM (e.g. `uom_purchase = box`, `uom_base = pcs`, factor = 12). Call
`post_purchase_invoice()` on unfixed code and assert that `qty_base` equals the converted value.
The assertion will fail, confirming the bug.

**Test Cases**:
1. **Different UOM — factor > 1**: Invoice line with `qty=10`, purchase UOM = box (factor 12 vs
   pcs). Assert `movement_line.qty_base == 120`. Will fail on unfixed code (`qty_base == 10`).
2. **Different UOM — factor < 1**: Invoice line with `qty=1000`, purchase UOM = g (factor 0.001
   vs kg). Assert `movement_line.qty_base == 1`. Will fail on unfixed code (`qty_base == 1000`).
3. **`total_cost` check**: For the same line, assert `total_cost == qty_base * unit_cost`. Will
   fail on unfixed code.
4. **Edge case — no buttons in range**: Invoice line with `qty=5`, purchase UOM = box (factor 6),
   `unit_cost=100`. Assert `total_cost == 3000`. Will fail on unfixed code (`total_cost == 500`).

**Expected Counterexamples**:
- `qty_base` equals `qty` (raw purchase quantity) instead of the converted base quantity.
- `total_cost` is computed from `qty` instead of `qty_base`, undervaluing or overvaluing inventory.

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the
expected behavior.

**Pseudocode:**
```
FOR ALL (line, product) WHERE isBugCondition(line, product) DO
  movement_line ← post_purchase_invoice_fixed(line, product)
  expected_base ← convert_qty(product.id, line.qty,
                               from_uom_id=effective_uom_id,
                               to_uom_id=product.uom_id)
  ASSERT movement_line.qty_base   = expected_base
  ASSERT movement_line.total_cost = expected_base * line.unit_price
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function
produces the same result as the original function.

**Pseudocode:**
```
FOR ALL (line, product) WHERE NOT isBugCondition(line, product) DO
  original_line ← post_purchase_invoice_original(line, product)
  fixed_line    ← post_purchase_invoice_fixed(line, product)
  ASSERT original_line.qty_base   = fixed_line.qty_base
  ASSERT original_line.total_cost = fixed_line.total_cost
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain (varying qty, unit_cost, UOM
  combinations where from == to).
- It catches edge cases that manual unit tests might miss (zero qty, very large quantities,
  fractional costs).
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs.

**Test Plan**: Observe behavior on unfixed code for same-UOM lines first, then write property-based
tests capturing that behavior and verify they still pass after the fix.

**Test Cases**:
1. **Same UOM preservation**: Invoice line where `line.uom_id == product.uom_id`. Assert
   `qty_base == qty` and `total_cost == qty * unit_cost` — same before and after fix.
2. **None UOM fallback preservation**: Invoice line where `line.uom_id` is None (falls back to
   `product.uom_id`). Assert `qty_base == qty` unchanged.
3. **Journal entry preservation**: Assert journal lines (DR/CR amounts) are derived from
   `subtotal`, not from `qty_base` — unaffected by the fix.
4. **Non-stock product preservation**: Invoice line for a product with `is_stock_item=False`.
   Assert no `StockMovementLine` is created — unchanged.

### Unit Tests

- Test `convert_qty()` is called with correct arguments when purchase UOM ≠ base UOM.
- Test `qty_base` equals converted quantity for factor > 1, factor < 1, and factor = 1.
- Test `total_cost` equals `qty_base * unit_cost` in all cases.
- Test that `line.uom_id = None` falls back to `product.uom_id` and produces `qty_base == qty`.
- Test that non-stock products produce no `StockMovementLine`.

### Property-Based Tests

- Generate random `(qty, factor)` pairs where `factor != 1` and verify
  `qty_base == qty * factor` after posting.
- Generate random same-UOM invoice lines and verify `qty_base == qty` (preservation).
- Generate random `unit_cost` values and verify `total_cost == qty_base * unit_cost` always holds.

### Integration Tests

- Post a full purchase invoice with mixed lines (some same-UOM, some different-UOM) and verify
  all `StockMovementLine` rows have correct `qty_base` and `total_cost`.
- Verify `post_movement()` computes the correct WAC after the fix (WAC uses `qty_base`).
- Verify journal entry amounts are unchanged (still based on invoice `subtotal`).
