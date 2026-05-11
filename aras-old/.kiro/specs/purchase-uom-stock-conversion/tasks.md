# Purchase UOM Stock Conversion — Implementation Tasks

## Tasks

- [-] 1. Write exploratory tests (unfixed code)
  - [ ] 1.1 Create `tests/test_erp/test_purchase_uom_stock_conversion.py` with a pytest fixture that sets up a product with a purchase UOM (box, factor=12) and a base UOM (pcs)
  - [ ] 1.2 Write test `test_qty_base_bug_different_uom`: post an invoice line with qty=10, purchase UOM=box; assert `movement_line.qty_base == 120` — this MUST FAIL on unfixed code to confirm the bug
  - [ ] 1.3 Write test `test_total_cost_bug_different_uom`: for the same line with unit_cost=50, assert `movement_line.total_cost == 6000` (120 * 50) — this MUST FAIL on unfixed code
  - [ ] 1.4 Run the exploratory tests against unfixed code and confirm they fail with `qty_base == 10` and `total_cost == 500`

- [ ] 2. Implement the fix in `purchase_posting.py`
  - [ ] 2.1 Add import: `from aras.erp.erp_stock.services.uom_service import convert_qty` at the top of `aras/erp/erp_acc/services/purchase_posting.py`
  - [ ] 2.2 Add `"base_uom_id": product.uom_id` to the dict appended to `stock_lines` inside the `if product and getattr(product, "is_stock_item", True):` block
  - [ ] 2.3 Before constructing `StockMovementLine`, compute `qty_base = convert_qty(sl["product_id"], sl["qty"], from_uom_id=sl["uom_id"], to_uom_id=sl["base_uom_id"])`
  - [ ] 2.4 Compute `total_cost = qty_base * sl["unit_cost"]`
  - [ ] 2.5 Update the `StockMovementLine(...)` constructor call to use `qty_base=qty_base` and `total_cost=total_cost` instead of the hardcoded expressions

- [ ] 3. Write fix-checking tests (Property 1)
  - [ ] 3.1 Write test `test_qty_base_fixed_different_uom`: post invoice line with qty=10, purchase UOM=box (factor=12); assert `movement_line.qty_base == 120`
  - [ ] 3.2 Write test `test_total_cost_fixed_different_uom`: assert `movement_line.total_cost == qty_base * unit_cost` for the same line
  - [ ] 3.3 Write test `test_qty_base_factor_less_than_one`: post invoice line with qty=1000, purchase UOM=g (factor=0.001 vs kg base); assert `movement_line.qty_base == 1`
  - [ ] 3.4 Run fix-checking tests and confirm they all pass

- [ ] 4. Write preservation-checking tests (Property 2)
  - [ ] 4.1 Write test `test_preservation_same_uom`: post invoice line where `line.uom_id == product.uom_id`; assert `qty_base == qty` and `total_cost == qty * unit_cost`
  - [ ] 4.2 Write test `test_preservation_none_uom`: post invoice line where `line.uom_id` is None (fallback to base UOM); assert `qty_base == qty`
  - [ ] 4.3 Write test `test_preservation_journal_entry`: post invoice and assert journal line amounts equal `subtotal` (not affected by UOM conversion)
  - [ ] 4.4 Write test `test_preservation_non_stock_product`: post invoice line for product with `is_stock_item=False`; assert no `StockMovementLine` is created
  - [ ] 4.5 Run preservation tests and confirm they all pass

- [ ] 5. Run full test suite and verify no regressions
  - [ ] 5.1 Run `pytest tests/test_erp/test_purchase_uom_stock_conversion.py -v` and confirm all tests pass
  - [ ] 5.2 Run `pytest tests/` and confirm no existing tests are broken
