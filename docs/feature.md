# Aras Framework Features

This document outlines the key features and architectural components of the Aras framework, including the recent **Aras Pro** enhancements.

## Core Architecture

-   **Metadata-driven Design:** Built on FastAPI and SQLAlchemy, enabling dynamic behavior and low-code extensibility through metadata.
-   **Hierarchical Structure:** A strict 3-level hierarchy ensures modularity and clear separation of concerns.
-   **Tiered Core Logic:** Prevents circular dependencies by organizing the core into Tiers (0: Utilities, 1: Logic, 2: API).

## Application Lifecycle Management

-   **`manage.py` CLI:** A central command-line interface for managing applications.
    -   `sync`: Synchronizes code-defined metadata to the DB registry and migrates the schema.
    -   `install <file>`, `uninstall <name>`, `activate`, `deactivate`, `discover`, `check`.

## Key Features & Capabilities

### Data & API Layer

-   **Generic CRUD Operations:** Automated generation of FastAPI endpoints via `RouterFactory`.
-   **Enhanced Querying:** Pagination, advanced filtering, and global search.
-   **Global Search & Command Center (Aras Pro):**
    -   **`CommandPalette`:** Integrated `CMD+K` interface for instant access to records, apps, and actions.
    -   **Robust Multi-Resource Search:** The `/search` API uses heuristic type detection and supports `__searchable_fields__` for fine-grained control.
    -   **Intelligent Labeling:** Automatically resolves display labels (username, number, title) for search results.
-   **Computed Properties (Aras Pro):** 
    -   **`@Aras.computed_field` Decorator:** Allows defining dynamic, read-only fields on models that are automatically serialized in API responses.
    -   **Serialization Flexibility:** Computed fields are seamlessly integrated into `to_dict()` and UI metadata.
-   **Advanced Relationship Management (Aras Pro):**
    -   **Many-to-Many (M2M) Support:** Automated M2M handling via `__m2m__` attribute, supporting bridge table synchronization and association management.
    -   **MultiSelect UI:** Dedicated `MultiSelectCombobox` for managing M2M relationships in the UI.
-   **Advanced Import Mapping (Aras Pro):**
    -   **Field Mapping UI:** Users can now map CSV columns to specific resource fields during the import process.
    -   **Background Processing:** Imports are handled via Celery for zero-latency user experience.
-   **Permissions & RBAC:** Integrated Role-Based Access Control.
-   **Auto-Migration:** Automatic database schema updates based on models.

### UI & Presentation Layer (Aras Pro Upgrades)

-   **Dynamic Analytics & Dashboard (Aras Pro):**
    -   **Pluggable Dashboard Widgets:** Support for Stat, List, and Chart widgets.
    -   **Interactive Data Visualization:** Built-in SVG-based charting engine supporting Bar and Pie charts with zero external dependencies.
    -   **Real-time Aggregation:** Widgets automatically fetch and group data from resources.
-   **Pro Layout Engine:**
    -   **Sections & Tabs:** Models can define `__layout__` to group fields into logical sections in the UI.
    -   **Dynamic Rendering:** `DynamicForm` automatically renders these layouts, reducing scroll fatigue.
-   **Advanced Conditional UI Visibility (Aras Pro):**
    -   **Safe `LogicEvaluator`:** A secure, recursive-descent logic engine for evaluating field dependencies (e.g., `total_amount > 5000 && status != 'Draft'`).
    -   **No-Eval Security:** Avoids unsafe JS execution, ensuring system stability.
-   **Pluggable UI Registry:**
    -   **`SchemaRegistry`:** A global registry for field components. Developers can easily register custom widgets (e.g., Color Pickers, Maps) without modifying core components.
-   **Real-time Validation:** Automated mapping of backend Pydantic errors (422) to UI field-level feedback.

### System & Extensibility

-   **Custom Model Actions Framework:**
    -   **`@Aras.model_action` Decorator:** Declarative business logic methods exposed as API endpoints.
    -   **UI Integration:** Actions appear as "Quick Action" (Zap icon) buttons in form headers.
-   **Centralized Background Task Processor:** Celery-powered task queue via `TaskManager`.
-   **Workflow Engine:** State-machine engine for document lifecycles.
-   **Advanced Logging and Monitoring:** Structured JSON logging and global exception handling.

---

## Framework Security Hardening

### Configuration & Secrets

-   **Centralized Settings (`api/core/lib/settings.py`):** Single source of truth for all environment config. Reads from `.env` via `python-dotenv`. `settings.validate()` is called at startup before any framework imports.
-   **Fail-Loud in Production:** `RuntimeError` if `SECRET_KEY` or `ARAS_ADMIN_PASSWORD` is missing in production mode. In development mode, an ephemeral key is generated with a warning.
-   **No Hardcoded Secrets:** All JWT keys, DB URLs, admin passwords, and CORS origins are env-driven. The `.env` file is the only place to configure these.

### API Security

-   **CORS Fixed:** `allow_origins=["*"]` + `allow_credentials=True` violated the CORS spec and was rejected by browsers. Now uses `settings.CORS_ORIGINS` (defaults to `http://localhost:5173`).
-   **All Admin/Dev Endpoints Authenticated:** Every `/api/v1/admin/*` and `/api/v1/dev/*` endpoint requires `require_admin` dependency (403 for non-admins, 401 for unauthenticated).
-   **Sidebar Authenticated:** `GET /api/v1/sidebar` requires `get_current_user`.
-   **File Download Protected:** `GET /api/v1/files/download/{filename}` requires auth + path traversal protection via `os.path.basename()`.
-   **Full RBAC on Query Endpoints:** `POST /{resource}/query` and `GET /search` both enforce `RBAC.has_permission()` for non-admin users. Global search uses a single bulk `get_readable_resources()` call to avoid N+1 queries.
-   **`require_admin` Single Source of Truth:** Defined once in `api/core/auth/service.py`; imported everywhere.

### Pydantic v2 Compliance

-   All `class Config: from_attributes = True` replaced with `model_config = ConfigDict(from_attributes=True)`.
-   All `@validator` decorators replaced with `@field_validator` + `@classmethod`.
-   All `.dict()` calls replaced with `.model_dump()` across `router_factory.py`, `installer.py`, and `dashboard.py`.

### Test Infrastructure

-   **`api/conftest.py`:** Session-scoped fixtures: `client` (TestClient), `admin_token`, `admin_headers`. Uses SQLite in-memory DB for isolation.
-   **`tests/test_auth_security.py`:** Verifies all secured endpoints return 401 without auth and 200 with admin token. Covers admin, dev, sidebar, and query endpoints.

### Performance Fixes

-   **N+1 RBAC Eliminated:** `global_search` now calls `RBAC.get_readable_resources()` once (single JOIN query) before the resource loop.
-   **Search Field Caching:** `_get_search_fields()` caches results on `model_class._search_fields_cache` — column iteration happens only once per model per process lifetime.
-   **Settings Seed Bulk Query:** Startup settings seed uses a single `IN` query instead of 8 individual SELECTs.
-   **Dead DB Connection Fixed:** `get_framework_info` no longer opens an unused DB connection.

### Frontend Reliability

-   **`ui/src/lib/resourceUtils.ts`:** `cleanResourcePath()` utility replaces 12+ inline path-normalization occurrences across `DynamicForm`, `ListView`, and `MetadataService`.
-   **React Error Boundary (`ErrorBoundary.tsx`):** Wraps the entire app; prevents blank screen on component errors. "Try Again" button resets state.
-   **MetadataService Caching:** In-memory `Map` cache with `clearCache()` and `invalidate()` methods. Prevents redundant `/metadata/` requests on re-navigation.
-   **API Error Shape Normalization (`api.ts`):** Response interceptor unifies `{message}` (backend custom handler) and `{detail}` (FastAPI 422) into a single `.detail` field.
-   **ERP Bootstrap Decoupled:** `erp_orders` widget removed from framework seed. App name reads from `settings.APP_NAME` env var.


## Change Logging Rule + Manual Log Command (2026-05-14)
  - [Claude Code] mhl command for manual change logging; --log-manual and --submit-review CLI flags; author+notes columns on dev_handoff_runs

## Framework Robustness & UI Completeness (2026-05-14)
- [Claude Sonnet 4.6] `api/core/lib/rate_limiter.py` — new RateLimiterMiddleware (sliding window, 200 req/60s default, 10/60s on auth endpoints)
- [Claude Sonnet 4.6] `api/core/logic/router_factory.py` — soft delete routing: `/deleted` list + `POST /{id}/restore` auto-generated for `__soft_delete__` models
- [Claude Sonnet 4.6] `api/core/base/field.py` + `router_factory.py` — declarative field validation rules: `min_length`, `max_length`, `min_value`, `max_value`, `pattern` wired into auto-generated Pydantic schemas
- [Claude Sonnet 4.6] `api/core/logic/router_factory.py` — batch API: `POST /batch` accepts up to 100 mixed create/update/delete ops atomically
- [Claude Sonnet 4.6] `api/core/api/websocket.py` — new WebSocket endpoint `/api/v1/ws?channel=` with JWT auth; `broadcast_sync()` helper for sync callers
- [Claude Sonnet 4.6] `ui/src/views/AuditLogs.tsx` — full audit log timeline with expandable diff viewer (before/after per field), action filter, pagination; replaces 21-line stub
- [Claude Sonnet 4.6] `ui/src/aras-core/components/DynamicForm.tsx` — client-side pre-validation (required, min/max length, min/max value, pattern) before submit; Field interface extended
- [Claude Sonnet 4.6] `ui/src/store/uiStore.ts` + `HeaderActions.tsx` + `index.css` — dark mode toggle with zustand/persist; `html.dark` class toggle; Tailwind v4 `@variant dark` configured
- [Claude Sonnet 4.6] `ui/src/aras-core/components/ListView.tsx` — bulk edit modal: select field + value, applies via `/batch` to all selected rows
- [Claude Sonnet 4.6] `ui/src/aras-core/components/ListView.tsx` — inline row editing: double-click text/number cell to edit in-place; Enter saves, Esc cancels
- [Claude Sonnet 4.6] `ui/src/aras-core/components/CommandPalette.tsx` — `?` key opens keyboard shortcut map modal; shortcut list accessible from palette footer


## Dashboard Drag-to-Rearrange + Audit Log Timeline View — revision (2026-05-14)
  - [Gemini] Added `POST /api/v1/dashboard/layout` endpoint for persisting user dashboard widget order.
  - [Codex/GPT-5.5] Native HTML5 drag-and-drop dashboard widget reordering with persisted widget_order POST to /dashboard/layout


## Dashboard drag-to-rearrange + Audit Log Timeline (2026-05-14)
  - [Claude Code] HTML5 drag-and-drop widget reorder,POST /dashboard/layout endpoint,GET/POST/PATCH /dev/dev_handoff_runs endpoints


## App Navigation Restructure — have_home + Topbar App Menu — revision (2026-05-14)
  - [Gemini] Implemented `have_home` attribute in `App` base class and app manifests; added `GET /api/v1/app-menu/{app_name}` endpoint.
  - [Codex/GPT-5.5] Flat app sidebar navigation, topbar app model tabs, generic app home landing page, and /:appName route

## Hierarchical Application Architecture (2026-05-15)

-   **Parent-Child App Relationships:** The `Aras.App` base class now supports a `parent_name` attribute, allowing applications to be organized into a hierarchy.
-   **Modular ERP Structure:** The ERP system has been refactored from a monolithic app into a set of specialized sub-apps (`accounting`, `stock`, `crm`, `pos`, `supplier`, `config`) nested under a primary `erp` parent.
-   **Recursive Sidebar Navigation:** The UI sidebar automatically detects and renders the application hierarchy, nesting sub-apps within their parents with visual indentation.
-   **Drill-Down App Home:** The `AppHome` view serves as a dashboard and module selector, displaying sub-apps as interactive tiles alongside primary models.
-   **Hierarchical Sync Engine:** `SyncManager` and `AppModel` now track and persist the application hierarchy in the database registry.

## Framework Robustness & GUI Enhancements (2026-05-15)

-   **Default ERP Dashboard Widgets:** Automated seeding of essential ERP analytics widgets (Total Products, Recent Movements, Financial Overview) during the sync process.
-   **Advanced Section-Based Layouts:** Core ERP models (SalesInvoice, JournalEntry, Product) now utilize the `__layout__` engine to organize fields into logical, titled sections in the UI.
-   **Automatic Invoice Logic:** Implementation of complex business logic for automatic recalculation of subtotals, taxes, and totals in the new `SalesInvoice` model, migrated from legacy codebase.
-   **Metadata Integrity Verification:** Enhanced health checks to ensure registry consistency across hierarchical application boundaries.



## Framework Refinements (2026-05-15)
- [Claude Opus 4.7] `api/core/base/model.py` — A1 `__unique_together__` composite UniqueConstraint applied in `__init_subclass__`; A4 removed baseline `is_active` (now opt-in `activatable` trait); A5 three-layer inheritance validation (single Level-3a abstract ancestor) + MRO merge of `__features__`/`__scoped_by__`/`__unique_together__`/`__layout__`
- [Claude Opus 4.7] `api/core/logic/trait_injector.py` — new `_inject_activatable` (opt-in `is_active` column) and `_inject_scoped` (auto FK columns from `__scoped_by__`, marked `form_hidden`)
- [Claude Opus 4.7] `api/core/logic/scope.py` (NEW) — `ScopeContext` request-scoped object + `scope_from_user` resolver
- [Claude Opus 4.7] `api/core/auth/service.py` — `get_current_user` now stashes `request.state.scope` from the JWT `scope` claim
- [Claude Opus 4.7] `api/core/auth/routes.py` — token endpoint includes `scope` claim; new `POST /api/v1/auth/switch-scope` re-issues JWT with updated scope
- [Claude Opus 4.7] `api/core/auth/models.py` — `User.current_company_id` nullable column added
- [Claude Opus 4.7] `api/core/logic/router_factory.py` — A2 narrows Pydantic type to `Literal[*choices]` when `info["choices"]` set; A3 list/get/create/update/patch routes filter by + auto-inject scope; dropped `is_active` special-case
- [Claude Opus 4.7] `api/core/logic/ui_generator.py` — A2 emits `select`/options for `info["choices"]`; honors `info["form_hidden"]`; exposes `scoped_by` at model level
- [Claude Opus 4.7] `api/core/registry/resource_model.py` — `scoped_by` JSON column added; `api/core/manager/sync_manager.py` persists it
- [Claude Opus 4.7] `api/core/logic/transition_registry.py` (NEW) — `TransitionRegistry` + decorator; `api/core/manager/workflow_manager.py` fires callbacks after status transition; `Aras.on_transition` exposed via `api/core/base/aras.py`
- [Claude Opus 4.7] `api/manage.py` — `sync` now runs `auto_migrate` before `sync_all` so new columns are present when registry queries run
- [Claude Opus 4.7] `api/core/registry/role.py`, `api/core/registry/permission.py` — opted into `__features__ = ["activatable"]` to keep `Role.is_active` / `Permission.is_active` after baseline removal
- [Claude Opus 4.7] `api/apps/_erp_base/{document,line_item,master_data,config}.py` (NEW) — Level-3a abstract bases for ERP modules (DocumentBase, LineItemBase, MasterDataBase, ConfigBase)
- [Claude Opus 4.7] `api/apps/{erp_config,erp_stock,erp_accounting,erp_crm,erp_supplier,erp_pos}/` (NEW) — six ERP app skeletons (manifest only, models empty)
- [Claude Opus 4.7] `api/apps/erp/` (DELETED) — legacy single-app ERP replaced by six properly-scoped modules

## UI Metadata & Relationship Fixes (2026-05-15)
- [Gemini] **Hybrid Metadata Child Table Fix**: Fixed issue where child tables defined in the database registry (LinkModel) were not appearing in the 'children' metadata, preventing them from being rendered in the parent form.
- [Gemini] **DynamicForm Child Table Rendering**: Updated `DynamicForm.tsx` to prevent redundant rendering of child table fields as text inputs in the main grid, ensuring they are only rendered as functional ListViews at the bottom of the form.

## Enhanced Child Table UI (2026-05-15)
- [Gemini] **Inline Child Table ListViews**: `DynamicForm` now renders `child_table` type fields as fully interactive `ListView` components directly within the form sections.
- [Gemini] **Smart Filter Correction**: Fixed parent-child filtering logic to use the internal resource name (table name) instead of the URL path for foreign key mapping (`parent_table_id`).
- [Gemini] **New Record Guard**: Child tables now display a friendly "Save first" message when creating a new record, preventing orphans and UI errors.

## UI Standardization for Child Tables (2026-05-15)
- [Gemini] **Generic Template Alignment**: Child tables now use the exact generic `ListView` template, ensuring full parity in capabilities (Search, Filters, Column Visibility, Bulk Actions, Export/Import).
- [Gemini] **Embedded Toolbar**: The native `ListView` toolbar is now used for child tables, providing a consistent UX across the entire platform.
- [Gemini] **Optimized Layout**: Removed redundant custom headers and styling overrides that previously deviated from the framework's standard UI patterns.


## InlineChildTable — extract to own file, fix double-wrap, clean toolbar — revision (2026-05-15)
  - [Codex/GPT-5.5] extracted InlineChildTable component with inline add/edit/delete row UI
