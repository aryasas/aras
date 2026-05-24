# Files Rule

This file is used only to report if there are fix


## Plan.md Full Build Queue — Backend 0, C1–C3, Backend 3–4, U4, U13, U14, Backend 6, H1–H2, R4, R6, H4, Backend 5+7–14, P1–P5, R1, R5, Backend 9–10, U1, U5, U2–U3, U6, U11 (2026-05-17)
  - [Gemini] Replaced all raw HTTPException raises in RouterFactory with appropriate custom ArasException subclasses, replaced all _create_success_response and _create_error_detail calls with new response.ok and response.err functions.
  - [Codex/GPT-5.5] dashboard dependency/catch/pie offset fixes, import endpoint switched to /import, console errors replaced with notifications in requested files, API path/error envelope normalization

## Backend Test Report (2026-05-17)

### GET /aggregate endpoint — FAIL
- status: Code does not execute due to upstream error
- issue: Router exception handler setup fails before aggregation code is reached (see below)

### Child hydration in GET /{id} — PASS (code verified)
- status: Code path verified in router_factory.py lines 387-440
- issue: None — implementation includes child_map traversal and child record hydration

### M2M in list — PASS (code verified)
- status: Code path verified in model.py lines 280-306
- issue: None — resolve_m2m() called automatically in paginate()

### Standard envelope — PASS (code verified)
- status: Response format verified in response.py
- issue: None — ok() returns {"success": true, "data": ..., "message": ..., "error": null}

### Exception handling (ResourceNotFoundException) — FAIL
- status: Exception defined but no app-level handler
- issue: router_factory.py line 94 uses @router.exception_handler() which does not exist on APIRouter (only on FastAPI app)

### Import endpoint — PASS (code verified)
- status: Endpoint exists at router_factory.py line 332
- issue: None — @router.post("/import") implemented with CSV file upload

### Computed fields in metadata — PASS (code verified)
- status: Code verified in ui_generator.py lines 239-252
- issue: None — computed fields marked with "computed": true in metadata response

## Summary of Issues

### CRITICAL
1. **Router exception handler registration fails**
   - Location: api/core/logic/router_factory.py, line 94
   - Error: `@router.exception_handler(ArasException)` — APIRouter doesn't support exception_handler as a decorator method
   - Impact: All dynamically-created routers fail to instantiate during app startup; prevents entire API from running
   - Root cause: Attempting to register exception handler on APIRouter instead of main app
   - Solution needed: Move exception handler registration to app-level in main.py, or use middleware instead

2. **Missing ArasException handler at app level**
   - Location: api/main.py
   - Issue: Custom ArasException subclasses (ResourceNotFoundException, ValidationException, etc.) are not handled by any app-level exception_handler
   - Impact: These exceptions will fall through to generic Exception handler, losing custom error formatting and status codes
   - Solution needed: Add @app.exception_handler(ArasException) in main.py before the generic Exception handler

### Testing Environment Issues (not blockers for actual deployment)
- Sandbox environment cannot establish network connections, preventing direct curl testing
- PostgreSQL database not available in test environment (tests require DATABASE_URL set to SQLite, but system defaults to Postgres)
- Tests cannot run locally due to exception handler setup failure

## Haiku QA Report (2026-05-17)

### CRITICAL
3. **accounting/services/conversion.py — AttributeError on party_id rename**
   - Location: api/apps/erp/accounting/services/conversion.py:13
   - Error: `order.customer_id` — model renamed field to `party_id`; AttributeError at runtime
   - Impact: Breaks `create_invoice` workflow entirely

4. **accounting/services/payment.py — Wrong field in query**
   - Location: api/apps/erp/accounting/services/payment.py:83
   - Error: `InflowInvoice.customer_id == party_id` — field is `party_id`; AttributeError at runtime
   - Impact: Breaks payment allocation

### MAJOR
5. **accounting/views.py — Layout references wrong field name**
   - Location: api/apps/erp/accounting/views.py:43, 55 (InflowOrderView, InflowInvoiceView)
   - Error: Field `customer_id` in layout; model uses `party_id` — causes form rendering/validation errors
   - Fix: Replace `customer_id` → `party_id` in these view layouts

### MINOR
6. **DashboardView.tsx — SVG strokeDashoffset type mismatch**
   - Location: ui/src/views/DashboardView.tsx:156, 165
   - Error: Numeric value where React SVG expects string; type mismatch in strict TS
   - Fix: Cast to string: `String(value)`

7. **InlineChildTable.tsx — Empty row filter runs after POST, not before**
   - Location: ui/src/aras-core/components/InlineChildTable.tsx:~80
   - Error: Empty rows may still be POSTed if filter logic only runs on display
   - Fix: Ensure filter runs as guard inside the submit handler before any POST call


## Unknown (2026-05-17)
  - [Codex/GPT-5.5] renamed organization picker file target and replaced stale companies references with organizations in DynamicForm

## Stock Module — on_transition + Service Compatibility Fixes (2026-05-17)
- [Claude Sonnet 4.6] Fixed `StockMovement.post` action to call `TransitionRegistry.get()` so `@Aras.on_transition` callbacks fire on status change (`api/apps/erp/stock/models.py`)
- [Claude Sonnet 4.6] Rewrote `posting.py` to use actual service signatures: `JournalService.post_entry()` (not `create_entry`), `InventoryValuationService` (not `FIFOValuation`), `CoaResolver` methods (not `COAResolver.resolve()`) (`api/apps/erp/stock/services/posting.py`)
- [Claude Sonnet 4.6] Fixed `valuation.py` to use `item_id` (renamed from `product_id`) and pass required `org_id`/`number` to `StockLayer` (`api/apps/erp/stock/services/valuation.py`)
- [Claude Sonnet 4.6] Fixed `coa_resolver.py` imports: `Product→Item`, `ProductCategory→ItemCategory` (`api/apps/erp/stock/services/coa_resolver.py`)
- [Claude Sonnet 4.6] Fixed `account.py` imports and `product_id→item_id` in filter (`api/apps/erp/stock/services/account.py`)
- [Claude Sonnet 4.6] Added `_save_children()` to `router_factory.py` — child table rows in parent POST/PATCH payload were silently dropped; now delete+re-insert on every write (`api/core/logic/router_factory.py`)


## Unknown (2026-05-17)
  - [Codex/GPT-5.5] reset child row ID baseline when loaded record ID changes


## Unknown (2026-05-17)
  - [Codex/GPT-5.5] normalized child table API path resolution so Price Rule deletes use the registered route

## COA Logic Fix & Validation (2026-05-19)
- [Gemini 2.5 Flash] `fill_default_accounts` now respects `coa_source_org_id`.
- [Gemini 2.5 Flash] Added `before_save` guard to `Organization` ensuring account-org integrity.

## Model Cleanup (2026-05-19)
- [Gemini 2.5 Flash] Removed redundant `sku` from `Item`.
- [Gemini 2.5 Flash] Refactored `ItemBundle` to inherit from `ErpBase` and use explicit `qty`.


## Unknown (2026-05-17)
  - [Codex/GPT-5.5] bulk delete verified as raw JSON array; vocabulary cache exported and refetch triggered on profile change


## Fix delete (single item and bulk) — still failing after previous attempts (2026-05-17)
  - [Codex/GPT-5.5] Fixed ListView delete and bulk-delete to use metadata-resolved API paths, refresh after deletion, clear deleted selections, and report backend bulk-delete counts correctly.


## Payment ↔ Invoice connection — manual allocation UI and deallocate action — revision (2026-05-18)
  - [Codex/GPT-5.5] Payment allocation rows now infer read-only invoice_type from parent payment_type

## Payment ↔ Invoice — rhf fixes (2026-05-18)
  - [Claude Sonnet 4.6] Reverted models.py import from `.base` to `..base` (agent broke parent package path)
  - [Claude Sonnet 4.6] Fixed app.py open_invoices route: replaced nonexistent `supplier_id` with `party_id`, added guard for null party_id, moved PaymentService import to lazy (top-level import caused ImportError via unrelated missing models)


## Fix Accounting Journal Balance & Party Transition (2026-05-18)
  - [Gemini 2.0 Flash] Fixed Journal not balanced error in OutflowInvoice by using purchase cost instead of COGS


## Advanced Account Resolution & Journal UI Fix (2026-05-18)
  - [Gemini 2.0 Flash] Fixed empty Account column in Journal Entry lines by explicitly setting lookup metadata and target API paths; Consolidated GoodsReceiptLine into main models file to resolve circular registration errors.


## ERP user access control (org-scoped RBAC) + fix module registration + rename UserRole.company_id → org_id — revision (2026-05-18)
  - [Gemini] Standardized ERP module registration (app_name, app_type), removed UserRole.company_id and integrated ERP org list in auth routes.


## Stock Breakdown & Table Rename (2026-05-19)
  - [Gemini 2.5 Flash] Fixed compute_qty to handle outflows correctly.


## Unknown (2026-05-19)
  - [Codex/GPT-5.5] DynamicView now handles delete and record navigation callbacks


## Unknown (2026-05-19)
  - [Codex/GPT-5.5] Styled child-table checkboxes and scrollbar


## Payment Party FK & Lookup (2026-05-19)
- [Gemini 2.5 Flash] Fixed `Payment.party_id` to be a real `ForeignKey` with proper UI lookup metadata.


## Tenant Admin UI (2026-05-19)
  - [Gemini 2.5 Flash] Fixed PotService stale imports and SQLAlchemy 2.0 query.get() deprecation warnings. Restored PotSession.orders relationship.


## Phase 4 — License enforcement + apps/saas/ MVP (2026-05-19)
  - [GPT (codex)] Replaced broken LicenseStatus UI imports with existing app components


## Phase 4 — License enforcement + apps/saas/ MVP — revision (2026-05-19)
  - [GPT (codex)] Fixed ContactView type-only React import for TypeScript build
## POS session list response normalization and sidebar active precision (2026-05-21)
- [GPT-5.5] Normalized POS list responses so `/erp/pot/pos` accepts framework paginated `{items}` payloads instead of crashing on `openSessions.map`.
- [GPT-5.5] Fixed sidebar active-state precision by removing over-wide fixed nav item widths and using a consistent active indicator inset.

## Dark-mode input styling and text legibility fixes (2026-05-21)
- [Antigravity] Replaced hardcoded inputs background (#f8fafc) and border (#dfe5ee) with CSS custom properties so that they respond dynamically to dark mode.
- [Antigravity] Fixed muddy-grey hardcoded text/label colors (#334155, #0f172a) in form controls using CSS variables, dramatically improving contrast and legibility under obsidian theme.


## CSS prefix migration & dark mode input fixes (2026-05-21)
  - [Antigravity] Dark mode form input background/border colors, hardcoded label/line text colors


## Test Database Configuration Alignment (2026-05-23)
  - [Gemini] Updated `tests/conftest.py` to allow `SQLALCHEMY_DATABASE_URI` to be overridden by an environment variable, defaulting to PostgreSQL. This aligns the testing environment with the project's "Hard Rules — Database" mandate, moving away from SQLite.
