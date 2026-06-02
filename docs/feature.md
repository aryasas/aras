## Docker Multi-Tenant E2E Stack (2026-05-30)
- [Gemini 2.5 Flash] Refreshed root `Dockerfile` and `ui/Dockerfile` with healthchecks and build arguments.
- [Gemini 2.5 Flash] Rewrote `docker-compose.yml` for a 4-tenant multi-container environment with shared tenant Postgres.
- [Gemini 2.5 Flash] Updated `api/core/tenant/provisioner.py` to support `TENANT_DB_*` environment variables for isolated DB host targeting.
- [Gemini 2.5 Flash] Added `TENANT_ID` environment variable support to `api/core/tenant/router.py` for dedicated tenant containers.
- [Gemini 2.5 Flash] Added `/api/v1/health` and `/api/v1/saas/control-panel/tenants/{tenant_id}/ping` endpoints for stack monitoring.
- [Gemini 2.5 Flash] Created `tests/e2e/test_docker_saas_flow.py` and `Makefile` for automated stack validation.

# Files Rule

This file is used only to report if there are feature added

# Aras Framework Features

## SaaS Polish & Backend Hardening (2026-05-29)
- [Gemini 2.5 Flash] Implemented pluggable EmailTransport system with SMTP, Resend, and Console backends.
- [Gemini 2.5 Flash] Developed automated dunning email service for overdue SaaS invoices.
- [Gemini 2.5 Flash] Added `fetch-geo` management command for GeoLite2 database maintenance.
- [Gemini 2.5 Flash] Hardened payment webhook handlers with signature verification and 400-error signaling.
- [Gemini 2.5 Flash] Established E2E test suite for Stripe, Midtrans, and Xendit webhooks with 100% pass rate.

## SaaS Phase 6–8 Backend (2026-05-29)
- [Gemini 2.5 Flash] Implemented pluggable payment provider architecture with Stripe, Midtrans, and Xendit.
- [Gemini 2.5 Flash] Added GeoMiddleware for IP-based payment provider routing.
- [Gemini 2.5 Flash] Developed Provisioner service for automated tenant DB creation and seeding.
- [Gemini 2.5 Flash] Implemented BillingService with automated invoice generation and APScheduler cron integration.
- [Gemini 2.5 Flash] Added RequestLog middleware and MetricsService for tenant usage monitoring.

## Quick Actions & Service Layer (2026-05-28)
- [Gemini] Added `GET /admin/quick-actions` returning RBAC-filtered actions, resources, and routes.
- [Gemini] Standardized `Aras.Service` base class for business logic with built-in RBAC and audit.
- [Gemini] Added `GET /web/landing/{key}` for targeted content retrieval.
- [Gemini] Added `reorder` action to `LandingSection` for manual sorting.
- [Gemini] Resource-specific `/search` and `/lookup` endpoints for optimized data retrieval.

## Metadata-driven UI, Profile Update & Framework Refactor (2026-05-29)
- [Gemini 2.5 Flash] Implemented `PUT /auth/me` and added `User.name` for profile management.
- [Gemini 2.5 Flash] Refactored `UIGenerator` to a Type Handler Pattern in `api/core/logic/ui_generator/`.
- [Gemini 2.5 Flash] Added `Model.get_ui_fields()` in `api/core/base/model/queries.py` for standardized column retrieval.
- [Gemini 2.5 Flash] Integrated `to_label_case` helper across the framework for consistent label generation.
- [Gemini 2.5 Flash] Added `ErpUserAccessView` and updated `OrganizationView` with UI type overrides for `profile`, `unit_type`, and `org_id`.

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

### Developer Tools
- Template Builder Persistence — `dev_template_annotations` table stores layout sections and AI annotations for system templates (Home, DynamicForm, etc.).

### Frontend Reliability
- `cleanResourcePath()` — centralizes path normalization
- API interceptor normalizes `{message}` and `{detail}` to `.detail`
- `api/pyrightconfig.json` — suppresses false-positive `reportMissingImports` on `core.*`

### Tests
- `conftest.py` — `client`, `admin_token`, `admin_headers` with SQLite in-memory DB
- `test_auth_security.py` — verifies 401 without auth, 200 with admin token on all secured endpoints

---

## 10. SaaS & Marketing
- **Customer Signups** — public `/signup` endpoint with email uniqueness check and `CustomerSignup` model.
- **Automated Provisioning** — `approve` action on `CustomerSignup` creates a `Subscription` with 14-day trial and auto-generated `tenant_id`.
- **Public Plan API** — `GET /plans/public` returns active plans ordered by price.
- **Customer Portal** — dedicated `/portal` for tenants to view subscription details and license tokens.
- **SaaS Portal Auth** — short-lived JWT issuance for tenants via `/portal/login`.
- **Marketing Content CMS** — `LandingSection` model for managing structured landing page content (hero, features, CTA, etc.) via admin UI.
- **Public Landing API** — `GET /landing` returns visible landing sections ordered by `sort_order`.
- **Tenant Configuration Delivery** — `GET /api/v1/saas/tenant-config` delivers plan configuration (active modules, limits) to tenant instances.
- **Module Enforcement** — `require_module` middleware for plan-based feature gating in tenant instances.

---

## 11. Infrastructure & DevOps
- **Dockerized Environment** — multi-container setup with PostgreSQL, Control Panel, Tenant Instance, and React UI.
- **Env Templates** — standardized `.env.example` for control-panel and tenant roles.

---

## Change Log (Condensed)

| Date | Key Changes |
|------|-------------|
| 2026-05-14 | Rate limiting, soft delete, batch API, WebSocket, audit log UI, dark mode, bulk edit, inline row editing, keyboard shortcut map, dashboard drag-to-rearrange, topbar app menu, `mhl` manual log command |
| 2026-05-15 | Hierarchical app architecture, ERP module split (7 sub-apps), scope system, transition registry, `__unique_together__`, child table UI standardization, ERP core features (charges, CRM, posting, payments), dual-axis navigation, mega-menu topbar, hierarchical URLs, Series rename, form customization UI, company-aware RBAC |
| 2026-05-16 | Reporting module, GRN + AP matching, financial reports, PostgreSQL migration, multi-tenant provisioner + REST API, demo/random invoice seeds, UI polish (empty states, skeletons, status badges, home cards), keyboard shortcuts, print/PDF, import validation, auto-discovery, saved filters, FIFO valuation, GL reconciliation, toast queue, dark mode charts |


## RouterFactory Aggregation & Action Wrapping (2026-05-26)
- [Gemini] Expanded `/aggregate` endpoint to support `min`, `max`, and `group_by` with subquery-based aggregation for performance and scope safety.
- [Gemini] Fixed custom action response wrapping in `RouterFactory` to avoid double `ok()` envelopes when handlers already return standardized responses.


## ARAS SaaS Production Readiness (2026-05-25)
- [Gemini 2.5 Flash] Implemented `GET /api/v1/saas/tenant-config` for plan delivery to tenants.
- [Gemini 2.5 Flash] Implemented `POST /api/v1/saas/license/renew` with trial support.
- [Gemini 2.5 Flash] Created `api/core/auth/module_guard.py` for plan-based module enforcement.
- [Gemini 2.5 Flash] Made `seed_default_plans` idempotent and non-overwriting.
- [Gemini 2.5 Flash] Added `.env.example` files and Docker configuration (Dockerfile, docker-compose.yml, ui/Dockerfile).

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

## Field Cleanup + Standalone Child View support (2026-05-18)
  - [Gemini 2.5 Flash] Introduced `View.standalone` flag to allow child models to appear in app menus.
  - [Gemini 2.5 Flash] Simplified `ItemUom` model and view, added `__scoped_by__` for org-level isolation of child records.


## Stock Breakdown & Table Rename (2026-05-19)
  - [Gemini 2.5 Flash] Added per-location stock calculation, API endpoint, and Item model computed field.


## Unknown (2026-05-19)

## Finance report consolidation (2026-05-19)
- [Gemini 2.5 Flash] Implemented P&L, Balance Sheet, and Trial Balance endpoints and service.
- [Gemini 2.5 Flash] Support for consolidated reports (HQ + mirrored organizations).

## Notes Entity (2026-05-19)
- [Gemini 2.5 Flash] Introduced centralized Note entity for record-level tracking.
- [Gemini 2.5 Flash] DocumentBase now supports note_id for persistent threading.


## Unknown (2026-05-19)
  - [Codex/GPT-5.5] Actions dropdown, column drag reorder, inline child row edit dialog, duplicate record button, FK add/edit navigation, note viewer, layout JSON customize panel


## LinkedDoc Auto-Discovery (2026-05-19)
- [Gemini 2.5 Flash] Refactored `Model.get_linked_documents` to use two-pass logic: SQLAlchemy inspection for automatic FK-based child discovery and explicit `__linked_docs__` declarations.
- [Gemini 2.5 Flash] Implemented automatic cascading soft-delete for discovered children in `Model._cascade_linked_docs`.

## Payment Invoices Prefill (2026-05-19)
- [Gemini 2.5 Flash] Added `get_open_invoices` model action to `Payment` to pre-fill allocation line items.

## POS Backend & Custom Routers (2026-05-19)
- [Gemini 2.5 Flash] Added `pos_session_id` tracking to Inflow/Outflow invoices.
- [Gemini 2.5 Flash] Implemented `POS` custom router with `/items` and `/quick_invoice` endpoints.
- [Gemini 2.5 Flash] Enhanced `PotSession` with computed shift summary fields (`total_sales`, `total_purchase`, `invoice_count`, `payment_summary`).

## Linked List Layout (2026-05-19)
- [Gemini 2.5 Flash] Added support for `type: "linked_list"` in layout JSON to render filtered embedded lists in forms.


## LinkedDoc auto-discovery, Payment fixes, POS view, Generic form tabs (2026-05-19)
  - [Codex/GPT-5.5] linked_list form tab rendering, model action allocation prefill handling, POS session view and route


## Tenant Admin UI (2026-05-19)
  - [Gemini 2.5 Flash] Added TenantAdmin view to manage multi-tenant dbs. Added POS receipt panel for completed orders.


## Phase 2 polish — tenant menu entry, POS session open flow (2026-05-19)
  - [GPT (codex)] Tenant Management settings entry for admins; POS no-session picker with open-session cards, new-session creation, and /erp/pot/pos route


## Phase 4 — License enforcement + apps/saas/ MVP (2026-05-19)
  - [GPT (codex)] License status/admin activation page, /admin/license route, Settings license entry, copyable token modal for model action responses


## Phase 4 — License enforcement + apps/saas/ MVP — revision (2026-05-19)
  - [GPT (codex)] CMS preview/public page routes, public contact form route, WebPage preview button in DynamicForm

## Docs Sync & SaaS Roadmap (2026-05-19)
- [Gemini 2.5 Flash] Synced `docs/aras.md` with app registration requirements and endpoint patterns.
- [Gemini 2.5 Flash] Merged `docs/saasplan.md` into `docs/plan.md` and marked completed phases.
- [Gemini 2.5 Flash] Created `tools/sync_reports.py` for docs/reports.json → DB synchronization.


## Docs sync, plan merge, reports sync, dev tools review, mock design proposals — revision (2026-05-19)
  - [GPT (codex)] Dashboard settings section and route; standalone ListView and FormView mock proposals; mock index entries
## Modern ERP Real UI Redesign (2026-05-21)
- [GPT-5.5] Added `ListViewActionBar` for one-bar list actions with Add New, search, filters, saved filters, view mode, columns, import/export, and archive controls.
- [GPT-5.5] Reworked real ListView/FormView/InlineChildTable surfaces toward the `erp-modern-app` mock with glass island panels, separated titles/actions, icon-only child table controls, and per-line pencil editing.
- [GPT-5.5] Revised DynamicForm field rendering from generic three-column grids to mock-style horizontal field rows, and changed InlineChildTable from a table grid to line-item rows matching the mock interaction pattern.
- [GPT-5.5] Tuned real form proportions directly against `ui/public/mocks/erp-modern-app/form.html` and `ui/public/mocks/erp-modern/form.html`: 24px islands, compact section headers, p-5 section bodies, 14px field controls, date sections as two-column grids, and line-item width/spacing.

## CSS prefix migration & dark mode input fixes (2026-05-21)
- [Antigravity] Migrated styling system to generic app- prefix inside ui/src/index.css, establishing an aliased selector mapping for 100% legacy compatibility.
- [Antigravity] Added Cross-Platform Design Token Dictionary mapping HSL colors for Expo/React Native sharing.
- [Antigravity] Reorganized action alignment by placing primary Save button (DynamicForm) and Add New button (ListToolbar) on the far left.


## CSS prefix migration & dark mode input fixes (2026-05-21)
  - [Antigravity] Left-aligned save action, generic styling layer migration, cross-platform Expo HSL design tokens


## Detailed Web Builder Styling & Inspector (2026-05-22)
  - [Gemini] Added properties inspector to TemplateBuilder for margin, padding, colors, alignment. LiveDesignWrapper applies these styles at runtime.


## In-Place WYSIWYG Design Mode (2026-05-22)
  - [Gemini] Transitioned from a macro Template Builder to a true in-place WYSIWYG element editor. Added DesignContainer and DesignElement primitives that intercept clicks and allow drag-and-drop. Created a global DesignInspector sidebar. Applied wrappers to DynamicForm and ListView components.


## In-Place WYSIWYG Design Mode (2026-05-22)
  - [Gemini] Fixed TemplateDesignToggle visibility by correctly injecting it into the Header. Changed toggle icon to Wand2 to distinguish it from standard editing. Added flex-shrink-0 to DesignInspector so it does not collapse. Refactored Header to use DesignContainer and DesignElement.


## Granular WYSIWYG & Dynamic Elements (2026-05-22)
  - [Gemini] Added dynamic element support to Design Mode (Text Block, Button, Divider, nested Containers). Added Add Elements palette to DesignInspector. Restructured ListViewActionBar with granular DesignContainers and DesignElements allowing per-button layout styling.

## Template Studio v3 (Craft.js) (2026-05-22)
- **Backend**: Extended `TemplateAnnotation` model, added `/dev_template_trees` and `/dev_template_annotations` endpoints, seeded default `erp-modern-invoice` tree, synced schema.

## Template Studio v3 (Craft.js) (2026-05-22)
- [Codex/GPT-5.5] Rewrote `ui/src/views/TemplateBuilder.tsx` into a Craft.js editor shell with responsive viewport controls, palette/outline/inspector panels, per-node AI note persistence, and breakpoint-driven canvas serialization.
- [Codex/GPT-5.5] Added Craft user-components and default serialized tree for the `erp-modern` invoice mock: responsive sidebar/header/islands, field grid + leaf controls, line-items composition, and dark summary/status islands.


## Unknown (2026-05-22)
  - [GPT (codex)] Craft.js Template Studio v3 matching the erp-modern invoice mock, with responsive viewport switching, default serialized tree loading, palette/outline/inspector/topbar panels, and per-node AI note persistence to dev template annotations.

## Core Model Refactoring & M2M Improvements (2026-05-23)
  - [Gemini] Refactored `api/core/base/model.py` for improved readability and maintainability:
    - Extracted `__init_subclass__` logic into dedicated helper methods (`_merge_inheritable_attributes`, `_register_model_and_validate_inheritance`, `_discover_child_relations`, `_discover_actions_and_computed_fields`, `_apply_unique_constraints`).
    - Enhanced error handling across multiple methods (`_discover_child_relations`, `_apply_unique_constraints`, `apply_filters`, `resolve_labels`, `resolve_m2m`, `save`, `_fire_hooks`) by replacing broad `except Exception` blocks with more specific `logging.error` or `logging.warning` with contextual messages.
    - Replaced raw SQL for Many-to-Many (M2M) operations in `resolve_m2m` and `save_m2m` with SQLAlchemy Core's `Table` objects, improving type safety and robustness.

## Router Factory Improvements & Streaming Export (2026-05-23)
  - [Gemini] Refactored `api/core/logic/router_factory.py` for improved modularity, error handling, and performance:
    - **Streaming Export:** Modified the `/export` endpoint to stream data directly from the database, significantly reducing memory consumption for large exports.
    - **Modular Child Operations:** Extracted complex child record synchronization logic from `_save_children` into dedicated module-level helper functions (`_update_or_create_child_record`, `_delete_orphaned_child_records`) for better readability and maintainability.
    - **Dynamic Schema Generation:** Extracted dynamic Pydantic schema generation (`Schema`, `PatchSchema`) into a new module-level helper function (`_generate_pydantic_schemas`), making `create_router` cleaner and more focused.
    - **Enhanced Error Handling:** Replaced generic `print` statements and broad `except Exception` blocks with specific `logging.warning` and `logging.error` calls across various endpoints and helper functions (e.g., custom actions, child hydration, bulk delete), providing more informative and actionable diagnostics.

## Mobile App — Metadata-Driven Expo — revision (2026-05-24)
  - [GPT (codex)] Metadata-driven Expo mobile app shell with auth, dynamic app/resource navigation, dynamic list view, and dynamic create/edit form rendering


## Production hardening — Customer SaaS portal + admin-controlled marketing pages + sidebar toggle stability — revision (2026-05-25)
  - [GPT (codex)] Public landing page, customer signup form, customer portal, public routes, login footer links, and full icon-rail collapse/restore control

## SaaS Admin REST Endpoints (2026-05-25)
  - [Gemini] Added 5 subscription management admin endpoints (list, approve, suspend, plan update, detail) to `api/apps/saas/routers.py`.

## Public SaaS pricing i18n and entitlement normalization (2026-05-26)
- [Codex/GPT-5.5] Added EN/ID public marketing and signup copy through `LanguageContext` and `ui/src/locales/{en,id}.json`.
- [Codex/GPT-5.5] Added public-page language toggles on the landing and signup pages.
- [Codex/GPT-5.5] Normalized SaaS plan payloads so `features.apps` is always present for plan cards and portal app gating.
- [Codex/GPT-5.5] Public pricing and signup now intentionally show the current customer-facing tiers only: Free, Lite, Growth, and Business.


## Framework remaining items — all NOT DONE and HALF from plan.md verified against actual codebase — revision (2026-05-26)
  - [GPT (codex)] Client-side form validation, M2M form field rendering/saving, form settings side panel, inline list editing, persisted column visibility, column resize/freeze, profile edit mode, command palette actions, frontend WebSocket connection


## Full sweep — immediate UX fixes + P0 in-flight close-out + P1 polish + P2 backend quality + P3 docs (2026-05-28)
  - [GPT (codex)] theme propagation, DB-driven landing sections, template memory/switching, robust websocket bridge, list/form live update handling, dirty-state guard, table accessibility/responsive behavior, quick-actions command palette, shared validation and list action helpers


## Remaining plan.md items — H3 typing, dark mode, dashboard DnD, table polish, profile edit, metadata-driven specials, Form Builder DnD, Framework Phases 1/2/3.1 (2026-05-29)
  - [GPT (codex)] metadata-driven profile/org/unit pickers, table column resize persistence support, dashboard preference-based reorder persistence, profile edit via PUT /auth/me, dnd-kit form layout editor with sections/tabs/preview


## SaaS Fase 6–8 — Auto-provisioning, automated billing, resource monitoring + Pluggable payment gateways (Stripe + Midtrans + Xendit) with IP-geo routing (2026-05-29)
  - [GPT (codex)] SaaS admin dashboard, tenant detail view, plan editor fields, SaaS admin routes/sidebar entry, checkout redirect signup flow, billing invoice/payment UI, redirect-back payment polling, and 402 billing redirect


## Polish sweep — FE silent-catch surfacing, `any` cleanup, email transport wiring, GeoLite2 bundling, payment webhook E2E tests — revision (2026-05-29)
  - [GPT (codex)] Surfaced portal fetch failures with safe API envelope parsing and error toasts; reduced `ui/src/aras-core/` explicit `any` usage to 37 while keeping `npm run build` green.


## Polish sweep — FE silent-catch surfacing, `any` cleanup, email transport wiring, GeoLite2 bundling, payment webhook E2E tests — revision (2026-05-29)
  - [GPT (codex)] Portal safe API envelope parsing with error toasts; aras-core explicit any count reduced to 37


## Config & Registry refinement — apps/core_config + ConfigRegistry + adjacent registries (Menu, Permission, Numbering, Jobs, Flags, Audit, Secrets, i18n) — revision (2026-05-29)
  - [GPT (codex)] Config workspace page with section rail, schema-driven forms, custom Company renderer, feature flags panel, config React Query helpers, account Workspace Settings link, required app badge/disabled uninstall state.


## Architecture cleanup — table prefix rename (`erp_`/`aras_` → `core_`/`<app>_`), Control Panel consolidation, Fixed Assets → accounting sub-module, license surface split — revision (2026-05-29)
  - [GPT (codex)] Control Panel routes, role gating, operator license panel, and control-panel test coverage


## Drop `aras_` prefix from DB names and localStorage keys — final naming cleanup — revision (2026-05-30)
  - [GPT (codex)] tenant localStorage key migration from aras_tenant_id to tenant_id


## Unknown (2026-05-30)
  - [GPT (codex)] Framework-owned /admin/settings UI with namespace rail, schema-driven section forms, section-level saves, URL namespace persistence, dirty-state handling, and settingsApi wrapper


## Unknown (2026-05-30)
  - [GPT (codex)] Master Data hub page, grouped rail, URL-persisted entity selection, ListView/DynamicForm embedding, API helpers, route, and Settings shortcuts


## Scale UI to match 110% browser zoom feel at 100% — revision (2026-06-01)
  - [GPT (codex)] Scaled requested UI sizing tokens, ARC atoms, list/header spacing, sidebar dimensions, and Lucide icon sizes to approximate 110% zoom at 100%


## Unknown (2026-06-01)
  - [GPT (codex)] Added Metadata Inspector, API Console, Error Log, and Cache & Registry tabs to DevTools


## Unknown (2026-06-01)
  - [GPT (codex)] DevTools command bar rewrite with adaptive canvas modes, scratchpad persistence, URL state, and keyboard shortcuts
