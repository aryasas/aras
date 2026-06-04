# Files Rule

This file is used only to report if there are fix


## Backend Hygiene & Script-Report Hardening (2026-05-29)
- [Gemini Flash] Implemented orphan-table drop policy in `auto_migrate.py`: only drops in `development` mode with explicit `--drop-orphans` flag in `manage.py sync`.
- [Gemini Flash] Hardened `exec()` in script reports: gated behind administrator role, restricted globals to a whitelist (no `__builtins__`), and added a 5-second timeout via `concurrent.futures`.
- [Gemini Flash] Added script approval tracking to `Report` model (`script_approved_by`, `script_approved_at`) and enforced it before execution.
- [Gemini Flash] Cleaned up bare `except:` blocks across `router_factory` and `model` packages, replacing them with specific exception handling and logging.
- [Gemini Flash] Migrated all `print()` statements to a proper logger in `discovery.py` and added a regression test.

## Plan.md Full Build Queue
 — Backend 0, C1–C3, Backend 3–4, U4, U13, U14, Backend 6, H1–H2, R4, R6, H4, Backend 5+7–14, P1–P5, R1, R5, Backend 9–10, U1, U5, U2–U3, U6, U11 (2026-05-17)
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


## Mobile App — Metadata-Driven Expo — revision (2026-05-24)
  - [GPT (codex)] Replaced starter App.js with App.tsx entry component


## Production hardening — Customer SaaS portal + admin-controlled marketing pages + sidebar toggle stability — revision (2026-05-25)
  - [GPT (codex)] Fixed same-path app icon navigation by refreshing location state and hiding the section panel when the icon rail is collapsed


## QA SWEEP — full-app regression test, report bugs only (NO FIXES) — revision (2026-05-25)
  - [GPT (codex)] Fixed frontend build blockers, restored DynamicForm model actions/display_token modal, added portal signup/landing error states, fixed mobile slash routes, removed dead mobile forgot button

## Sidebar Menu Stability and Sub-app Redirection (2026-05-25)
  - [Gemini] Fixed `Sidebar.tsx` to correctly flatten non-grouped menu items and include sub-apps that are not explicitly in `menu_groups`.
  - [Gemini] Fixed `SmartDispatcher.tsx` to use the full matched app path for menu fetching and correctly determine the first menu item for redirection, preventing sub-apps from being redirected back to their parent app's home.

## Sidebar Toggle Expanded State with Text (2026-05-25)
  - [Gemini] Enhanced `Sidebar.tsx` to support an expanded state for the app rail. When `sidebarCollapsed` is false, the app rail expands to 180px and displays text labels next to icons, while also showing the section submenu panel.
  - [Gemini] Added user profile summary and notification labels to the expanded sidebar for better UX.

## UndefinedColumn Error in Reports Fixed (2026-05-25)
  - [Gemini] Fixed `ProgrammingError: column si.total_amount does not exist` in accounting reports.
  - [Gemini] Refactored `InflowInvoice` and `OutflowInvoice` to use `DocumentRecalcMixin` and added `subtotal`, `total_charge`, and `total_amount` as persistent `Float` columns.
  - [Gemini] Populated missing totals for existing records via a one-time maintenance script.
  - [Gemini] Ensured consistent naming of totals in both models and reports to allow for raw SQL queries.

## Audit hardening follow-up and public SaaS plan/i18n fixes (2026-05-26)
- [Codex/GPT-5.5] Tightened request scope handling so unsupported `X-Scope-*` headers are rejected and `X-Org-ID` cannot conflict with `X-Scope-Org-ID`.
- [Codex/GPT-5.5] Fixed generic bulk delete and batch operations to fail on missing/out-of-scope records and commit successful list-shaped batch writes atomically.
- [Codex/GPT-5.5] Removed implicit non-null FK auto-cascade deletes; destructive cascades now require explicit `LinkedDoc(cascade=True)` declarations.
- [Codex/GPT-5.5] Restricted startup sync/bootstrap writes to non-production modes.
- [Codex/GPT-5.5] Moved browser auth JWT storage from persistent `localStorage` to `sessionStorage` with legacy token cleanup.
- [Codex/GPT-5.5] Fixed public SaaS pricing/signup pages to show only the current public plans (`free`, `lite`, `growth`, `business`) and to use EN/ID language strings.

## Framework Quality Fixes (2026-05-26)
- [Gemini] Fixed `strokeDashoffset` SVG attribute in `DashboardView.tsx` by removing redundant `String()` wrapper, satisfying SVG attribute numeric type requirements.
- [Gemini] Added missing `key` fields to `PotSessionView` layout definitions in `pot/views.py` to ensure consistent rendering and prevent React key warnings.
- [Gemini] Renamed "Totals" tab to "Financials" in `InflowInvoiceView` and `OutflowInvoiceView` within `accounting/views.py` to align with organizational naming standards.


## Framework remaining items — all NOT DONE and HALF from plan.md verified against actual codebase — revision (2026-05-26)
  - [GPT (codex)] Typed SchemaRegistry FieldProps and wired InlineChildTable lookup cache


## Full sweep — immediate UX fixes + P0 in-flight close-out + P1 polish + P2 backend quality + P3 docs (2026-05-28)
  - [GPT (codex)] removed ListViewActionBar shim, added login-card test id, normalized preference endpoints, added metadata flush after FormSettings save, fixed build-blocking unused InlineChildTable declarations

## Backend Sweep Revision & UX Polish (2026-05-29)
- [Gemini 2.5 Flash] Deleted stale `.bak` files from core split (`model.py.bak`, `router_factory.py.bak`).
- [Gemini 2.5 Flash] Created shared `SkeletonRow` component and consolidated pulse animations across `ArasTable` and `ListView`.
- [Gemini 2.5 Flash] Verified backend integrity via full smoke test suite (14/14 pass).

## Framework Import & Metadata Fixes (2026-05-29)
- [Gemini 2.5 Flash] Fixed `ModuleNotFoundError` during sync by correcting relative imports in `api/core/logic/ui_generator/__init__.py`.
- [Gemini 2.5 Flash] Corrected `ResourceModel.layout` type hint to `list` to match `View.layout` structure.
- [Gemini 2.5 Flash] Fixed `NameError: to_label_case` in `UIGenerator` by adding missing import.


## Remaining plan.md items — H3 typing, dark mode, dashboard DnD, table polish, profile edit, metadata-driven specials, Form Builder DnD, Framework Phases 1/2/3.1 (2026-05-29)
  - [GPT (codex)] removed downstream field renderer any casts in DynamicForm/ListView; corrected Profile save endpoint and topbar user update

## Public-page error UX and mobile auth headers (2026-05-29)
- [Codex/GPT-5.5] Added retryable error states for public landing and signup plan loading, normalized customer portal envelope parsing with raw JSON fallback, and wired mobile API auth/org headers through AsyncStorage-backed helpers.


## Close all outstanding QA/audit items from plan.md Section 7 — backend hygiene, public-page error UX, script-report sandbox, mobile auth audit (2026-05-29)
  - [GPT (codex)] Public signup/landing retry error UX, portal envelope parsing with legacy fallback, mobile AsyncStorage auth/org headers, ResourceList 401/403 error state


## SaaS Fase 6–8 — Auto-provisioning, automated billing, resource monitoring + Pluggable payment gateways (Stripe + Midtrans + Xendit) with IP-geo routing (2026-05-29)
  - [GPT (codex)] Removed unused dashboard import found during build


## Polish sweep — FE silent-catch surfacing, `any` cleanup, email transport wiring, GeoLite2 bundling, payment webhook E2E tests — revision (2026-05-29)
  - [GPT (codex)] <description, or "none">


## Polish sweep — FE silent-catch surfacing, `any` cleanup, email transport wiring, GeoLite2 bundling, payment webhook E2E tests — revision (2026-05-29)
  - [GPT (codex)] Fixed TypeScript fallout from tighter aras-core component types; npm run build passes


## Config & Registry refinement — apps/core_config + ConfigRegistry + adjacent registries (Menu, Permission, Numbering, Jobs, Flags, Audit, Secrets, i18n) — revision (2026-05-29)
  - [GPT (codex)] Sidebar fetch now prefers /menu with /sidebar fallback; i18n context attempts merged backend bundles with local fallback.


## Architecture cleanup — table prefix rename, Control Panel consolidation, Fixed Assets -> accounting sub-module, license surface split (2026-05-29)
  - [Gemini 2.5 Flash] Renamed legacy aras_* and erp_* framework/app tables to core_* and <app>_*. Consolidated Control Panel and separated tenant-facing and operator-facing license interfaces. Moved Fixed Assets (apps/asset) to an accounting sub-module (apps/accounting/assets).


## Architecture cleanup — table prefix rename (`erp_`/`aras_` → `core_`/`<app>_`), Control Panel consolidation, Fixed Assets → accounting sub-module, license surface split — revision (2026-05-29)
  - [GPT (codex)] Removed TenantAdmin view, redirected legacy SaaS Admin routes, renamed SaaS Admin labels/API paths to Control Panel


## Drop `aras_` prefix from DB names and localStorage keys — final naming cleanup — revision (2026-05-30)
  - [GPT (codex)] updated frontend tenant storage key usage and covered legacy/new/empty storage cases


## Unknown (2026-05-30)
  - [GPT (codex)] Redirected old /settings navigation to /admin/settings and removed old /config route target references from frontend navigation


## Unknown (2026-05-30)
  - [GPT (codex)] Sidebar dynamic app loop now skips apps with hide_from_sidebar


## Unknown (2026-06-01)
  - [GPT (codex)] Removed old tab system, sidebar nav, and command palette modal


## Unknown (2026-06-03)
  - [GPT (codex)] Replaced demo form/home content, added MobileShell navigation prop usage, dynamic metadata choice chips


## Mobile production-ready: 401 interceptor, metadata-driven form, pagination, real dashboard, navigation wiring (2026-06-03)
  - [GPT (codex)] Removed ARC-PLM demo content, replaced hardcoded filters with dynamic choices, wired MobileShell navigation prop


## Unknown (2026-06-03)
  - [GPT (codex)] Required-field validation, 422 parsing, delete action, new-record shell title, select option coercion, and filter refetch behavior


## Unknown (2026-06-03)
  - [GPT (codex)] wired dead settings actions, added pull-to-refresh and keyboard-aware forms, added save/delete toasts and haptics, and routed network failures into inline/offline states instead of dead-end errors


## Unknown — revision (2026-06-03)
  - [GPT (codex)] Replaced the brittle expo-constants deep import with a direct package import and implemented the run-106 POS screen revision spec


## Unknown (2026-06-03)
  - [GPT (codex)] updated profile persistence to PUT /auth/me with name and email, renamed auth state to name, enabled StatusBar auto, added axios timeout, capped POS cart quantities at stock, added logout confirmation


## Unknown (2026-06-03)
  - [GPT (codex)] Auto-load by id, paged list loading, dirty/reset/submit handling


## Global Market Compliance — PCI-DSS, GDPR, PDPA, Password Policy, Audit PII Masking, Timezone UTC, Currency i18n (2026-06-03)
  - [GPT (codex)] removed hardcoded currency literals from the requested views, replaced currency helpers with shared formatter usage, and added aria-live/skip-link/nav semantics


## Global Market Compliance — PCI-DSS, GDPR, PDPA, Password Policy, Audit PII Masking, Timezone UTC, Currency i18n — revision (2026-06-03)
  - [GPT (codex)] replaced the empty currency fallback in the hero subtitle with the existing localized pricing helper


## Global Market Compliance — PCI-DSS, GDPR, PDPA, Password Policy, Audit PII Masking, Timezone UTC, Currency i18n — revision (2026-06-03)
  - [GPT (codex)] added translations for validation, not found, auth, and permission error codes


## RBAC tiering — framework owns the model/loader; apps own their permission data; product roles stay in the Settings app. Rename apps/config → apps/settings. Add `App.rbac_file` convention + `get_custom_permissions()` hook. — revision (2026-06-04)
  - [Gemini (gemini-3-flash-preview)] Renamed config app to settings to resolve architectural coupling.


## Unknown (2026-06-04)
  - [GPT (codex)] removed apps.base package/shim, repointed imports, and dropped the plugin apps.base isolation exception


## Unknown (2026-06-04)
  - [GPT (codex)] updated seed import path, removed stale apps/demo usage, refreshed apps-tier docs


## Unknown (2026-06-04)
  - [GPT (codex)] Company and Localization marked as first-run setup steps; settings router mounted so /settings/setup is reachable


## Unknown (2026-06-04)
  - [GPT (codex)] seed catalog now includes convention RBAC and demo seed entries; oversell blocking, journal balancing, and payment over-allocation now raise validation errors correctly


## Unknown (2026-06-04)
  - [GPT (codex)] GET /accounting/organizations/{org_id}/vocabulary now resolves profile defaults when override rows are absent, profile vocabulary upserts are idempotent, manual vocabulary writes now satisfy OrganizationVocabulary table requirements
  - [GPT (codex)] Removed hardcoded profile picker options, eliminated duplicated frontend profile defaults in favor of the profiles endpoint, and kept vocabulary cache invalidation in sync after profile changes


## Unknown (2026-06-04)
  - [GPT (codex)] Made widget seeding idempotent across sync/bootstrap and prevented trade widgets from leaking into non-trade default dashboards
  - [GPT (codex)] removed the TradeDashboard home fork and deleted the unused TradeDashboard view


## Unknown — revision (2026-06-04)
  - [GPT (codex)] <short description or 'none'>
  - [GPT (codex)] <short description or 'none'>
