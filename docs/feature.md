# Files Rule

This file is used only to report if there are feature added

# Aras Framework Features

---

## 1. Core Architecture
- Metadata-driven design (FastAPI + SQLAlchemy)
- 3-level hierarchical structure
- Tiered core logic (Tier 0: Utilities, Tier 1: Logic, Tier 2: API)
- Hierarchical app architecture — `parent_name` on `Aras.App`, persisted in DB registry
- Inheritance-based registration — ERP sub-apps inherit from base `ERP` class

---

## 2. Application Lifecycle (`manage.py`)
- `sync` — auto-migrates schema before syncing metadata
- `install`, `uninstall`, `activate`, `deactivate`, `discover`, `check`
- `seed` — ERP seeding (COA, Currencies, UOMs, Warehouses)
- `tenant provision|list|seed|deprovision`

---

## 3. Data & API Layer

### CRUD & Querying
- Generic CRUD via `RouterFactory`
- Pagination, filtering, global search
- Soft delete — `__soft_delete__` adds `/deleted` + `POST /{id}/restore` automatically
- Batch API — `POST /batch` up to 100 mixed ops, atomic

### Search
- `CommandPalette` (`CMD+K`)
- Multi-resource `/search` with `__searchable_fields__`
- Auto-resolved display labels per resource

### Fields & Validation
- `@Aras.computed_field` — read-only dynamic fields, auto-serialized
- Declarative validation — `min_length`, `max_length`, `min_value`, `max_value`, `pattern` on `Aras.Field`
- `info["choices"]` — narrows Pydantic type to `Literal[*choices]`, renders select in UI

### Relationships
- M2M via `__m2m__` with bridge table sync
- Child tables rendered as embedded `ListView` with FK filtering and "Save first" guard

### Scoping & Multi-Tenancy
- `__scoped_by__` — auto-injects FK columns, filters all routes by scope from JWT claim
- `POST /api/v1/auth/switch-scope` — re-issues JWT with new scope
- `X-Company-ID` header for company-aware RBAC
- Multi-tenant provisioner — per-tenant PostgreSQL DB, `metadata.create_all`, `auto_migrate`, soft-delete via `ALTER DATABASE RENAME TO`
- Tenant REST API — `GET/POST/DELETE /tenants/*` (superuser only)

### Real-Time
- WebSocket `/api/v1/ws?channel=` with JWT auth + `broadcast_sync()` helper

---

## 4. Model Internals
- `__unique_together__` — composite `UniqueConstraint` in `__init_subclass__`
- `__features__ = ["activatable"]` — opt-in `is_active` column (removed from baseline)
- Three-layer inheritance validation — single Level-3a abstract ancestor, MRO merge of `__features__`, `__scoped_by__`, `__unique_together__`, `__layout__`
- `@Aras.on_transition` — transition registry; `WorkflowManager` fires callbacks on status change
- `@Aras.model_action` — exposes methods as API endpoints + "Quick Action" buttons in UI
- Saved filters — per-user filter persistence (model + router + registration)
- Auto-discovery — ERP models discovered without explicit registration

---

## 5. UI & Presentation

### Forms
- `__layout__` — named sections and tabs in `DynamicForm`
- Form customization — settings button in header to override `default_value` and `series` per field
- Series generation — auto-generates sequential IDs (e.g., `INV-2026-0001`) on create
- `LogicEvaluator` — safe recursive-descent engine for conditional field visibility
- Client-side pre-validation before submit
- Backend 422 errors mapped to field-level feedback
- `Ctrl+S` save, `Esc` cancel
- Animated skeleton during form load

### Lists
- Inline row editing — double-click to edit, Enter/Esc
- Bulk edit modal — applies one field value to all selected rows via `/batch`
- Smart empty state — "Add New" vs "Clear filters" depending on active filters
- Status badges — colored pills for `status`/`workflow_status` columns
- `ListToolbar` — shared across standalone lists and inline child tables

### Dashboard & Navigation
- Pluggable widgets: Stat, List, Chart (SVG-based, no external deps)
- Dashboard drag-to-rearrange with `POST /dashboard/layout` persistence
- StatWidget/ListWidget rows navigate to resource on click
- Dual-axis navigation — Sidebar for root apps, Topbar for app-specific resources
- Mega-menu Topbar — sibling modules as top-level dropdown groups
- Sidebar reserved for root apps only; active parent highlighted when in sub-app
- Dynamic AppHome tiles from `menu_groups` / `sub_apps`

### URL & Routing
- Hierarchical hyphenated URLs (e.g., `/erp/accounting/accounts`)
- Prefix stripping — `erp_accounting_` removed from UI labels
- `SmartDispatcher` — resolves URL segments to App Home or Resource view
- API paths mirror frontend hierarchy

### Other
- Dark mode (Zustand persist, `html.dark`, dark-aware charts)
- Audit log timeline with expandable field diffs, action filter, pagination
- Print/PDF preview modal (`window.print()`)
- Home cards — greeting + app cards above dashboard
- React Error Boundary with "Try Again"
- `SchemaRegistry` — register custom field widgets without touching core

---

## 6. ERP Module

### Structure
- 7 sub-apps: `accounting`, `stock`, `crm`, `pos`, `supplier`, `config`, `report`
- Level-3a abstract bases: `DocumentBase`, `LineItemBase`, `MasterDataBase`, `ConfigBase`
- `NamingSeries` → renamed to `Series`

### Documents & Finance
- Sales Orders, Purchase Orders, Delivery Notes, GRN, Payment Allocations
- Auto-posting — "Post" action generates balanced Journal Entries via heuristic account mapping
- Auto-recalculation of subtotals, taxes, totals on `SalesInvoice`
- `amount_paid` / `amount_due` as `@Aras.computed_field` on invoices
- Charge registry — Percent/Fixed, inclusive/exclusive, GL account linkage
- `ModeOfPayment` with per-company COA mapping
- Fiscal Period management; POS Terminal configs (warehouse/pricelist overrides)
- FIFO inventory valuation
- GL reconciliation (service + model action)

### CRM
- Leads, Opportunities, Pipelines with customizable stages and probability

### Reporting
- `erp_report` sub-app centralizes all reports
- `ReportService` executes query-type reports via `QueryBuilder`
- Financial reports: Trial Balance, P&L, AR Aging, AP Aging
- Action buttons use action `label` dynamically (no hardcoded "Run")
- Report Center filters with `today` parameter resolution in SQL

### Import
- CSV column mapping UI
- Validation preview step before posting
- Background via Celery

---

## 7. System & Extensibility
- `RateLimiterMiddleware` — 200 req/60s general, 10/60s on auth endpoints
- Celery task queue via `TaskManager`
- Workflow engine (DB-driven state machine)
- Structured JSON logging + global exception handling
- `TranslationService` — metadata i18n (app names, titles, labels); `lang` param on API
- Toast notification queue

---

## 8. Security & Performance

### Security
- `settings.validate()` at startup — `RuntimeError` if secrets missing in production
- CORS via `settings.CORS_ORIGINS`
- `require_admin` dependency (single source of truth) on all `/admin/*` and `/dev/*` endpoints
- File download: auth + `os.path.basename()` path traversal protection
- Pydantic v2 — `model_config`, `@field_validator`, `.model_dump()` throughout

### Performance
- N+1 RBAC eliminated — single `get_readable_resources()` JOIN in global search
- `_get_search_fields()` cached on `model_class._search_fields_cache`
- Settings seed uses single `IN` query
- `MetadataService` in-memory cache with `clearCache()` / `invalidate()`

### Frontend Reliability
- `cleanResourcePath()` — centralizes path normalization
- API interceptor normalizes `{message}` and `{detail}` to `.detail`
- `api/pyrightconfig.json` — suppresses false-positive `reportMissingImports` on `core.*`

### Tests
- `conftest.py` — `client`, `admin_token`, `admin_headers` with SQLite in-memory DB
- `test_auth_security.py` — verifies 401 without auth, 200 with admin token on all secured endpoints

---

## 9. Infrastructure
- PostgreSQL (`psycopg2`, port 5432)
- Multi-tenant: per-tenant DB provisioning, `auto_migrate`, soft-delete via DB rename

---

## Change Log (Condensed)

| Date | Key Changes |
|------|-------------|
| 2026-05-14 | Rate limiting, soft delete, batch API, WebSocket, audit log UI, dark mode, bulk edit, inline row editing, keyboard shortcut map, dashboard drag-to-rearrange, topbar app menu, `mhl` manual log command |
| 2026-05-15 | Hierarchical app architecture, ERP module split (7 sub-apps), scope system, transition registry, `__unique_together__`, child table UI standardization, ERP core features (charges, CRM, posting, payments), dual-axis navigation, mega-menu topbar, hierarchical URLs, Series rename, form customization UI, company-aware RBAC |
| 2026-05-16 | Reporting module, GRN + AP matching, financial reports, PostgreSQL migration, multi-tenant provisioner + REST API, demo/random invoice seeds, UI polish (empty states, skeletons, status badges, home cards), keyboard shortcuts, print/PDF, import validation, auto-discovery, saved filters, FIFO valuation, GL reconciliation, toast queue, dark mode charts |


## Plan.md Full Build Queue — Backend 0, C1–C3, Backend 3–4, U4, U13, U14, Backend 6, H1–H2, R4, R6, H4, Backend 5+7–14, P1–P5, R1, R5, Backend 9–10, U1, U5, U2–U3, U6, U11 (2026-05-17)
  - [Gemini] Custom exception classes (ArasException and subclasses), standardized API response functions (ok, err), FastAPI exception handlers for custom exceptions.
  - [Codex/GPT-5.5] dashboard widget registry, batch child create flow, m2m form support, inline child lookup cache/editing, archive view and restore flow, shared UI/helper primitives

## Stock Module Item Rename + Full Port Spec (2026-05-17)
- [Claude Sonnet 4.6] Wrote docs/handoff.md spec: Product→Item rename across all stock models/views/services, ItemBundle M2M model, ItemLocation model, @Aras.on_transition posting service, WAC+FIFO fix, workflow fix, company→org rename (backend header + frontend localStorage/authStore)

## Stock Module — Full Integration Test Pass (2026-05-17)
- [Claude Sonnet 4.6] Verified end-to-end stock receipt posting: SM-002 (receipt, 2 lines) → Post action → `on_transition` fires → WAC computed → FIFO layers created → GL skipped gracefully (no COA for test org)
- [Claude Sonnet 4.6] Verified child row persistence: ItemBundle (M2M components) and ItemLocation saved via `_save_children()` framework fix
- [Claude Sonnet 4.6] Verified `TransitionRegistry` wiring: `StockMovement.post` now calls `TransitionRegistry.get()` to fire all registered `@Aras.on_transition` callbacks


## Unknown (2026-05-17)
  - [Codex/GPT-5.5] child table removed row tracking and DELETE persistence on save


## Unknown (2026-05-17)
  - [Codex/GPT-5.5] per-row delete button in ListView; organization save updates authStore profile and clears vocabulary cache


## Payment ↔ Invoice connection — manual allocation UI and deallocate action — revision (2026-05-18)
  - [Gemini] Added payment-invoice connection functionality including computed fields, model actions, view configurations, and a new API endpoint for open invoices.
  - [Codex/GPT-5.5] Added child-table async invoice selection for payment allocations and deallocate-backed remove action


## Fix Accounting Journal Balance & Party Transition (2026-05-18)
  - [Gemini 2.0 Flash] Standardized party_id across all invoice types


## Advanced Account Resolution & Journal UI Fix (2026-05-18)
  - [Gemini 2.0 Flash] Added display_name (Code - Name) to Account for better UI selection; Enhanced CoaResolver to support Chart of Accounts mirroring via coa_source_org_id.


## ERP user access control (org-scoped RBAC) + fix module registration + rename UserRole.company_id → org_id — revision (2026-05-18)
  - [Gemini] Implemented ERP org-scoped RBAC with new model and 5 endpoints.
  - [Codex/GPT-5.5] ERP User Access settings page with user access table, scope badges, admin handling, slide-in editor, org checklist, save and revoke actions


## Hierarchical org scope expansion & is_shared master data (2026-05-18)
  - [Gemini 2.5 Flash] Hierarchical org scope expansion (top-down for groups, bottom-up for leaf orgs), is_shared flag on MasterDataBase


## Hierarchical org scope expansion — parent/child data sharing + is_shared flag on master data — revision (2026-05-18)
  - [Codex/GPT-5.5] Added is_group support to Organization type and Consolidated badge beside the org switcher for group organizations
