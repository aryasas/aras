
# Aras Framework: Technical Report & Architecture Guide

Jika saya mengatakan:
"'dde', artinya 'don't do edit' — jangan lakukan perubahan apapun."
"'rrc', artinya 're read CLAUDE.md' — before anything else, re-read CLAUDE.md rules 1-3"
- if i say cmp mean "inspect/review my project. what can we add to project to make more robust, complete, nice gui. before we move to create an app? inpect code, function, and ui (easyness, posisiton, and aesthetic). and as you go, if you find something repeatable, refactor it."
- if i say ggc mean "give git commit command text with message all we do/add to project but you DONT exec/git, i will do the git myself."
- if i say updd mean "update/edit feature.md to add what we do/add to the project (dont delete just add/update) and update/edit aras.md (if needed, dont delete except there are something changed make aras.md irrelevan)"

## 1. System Overview
Aras is a metadata-centric application framework designed for extreme developer productivity. It follows a **Code-First, GUI-Override** philosophy where the database acts as a registry for code-defined models.

## 2. Inheritance Hierarchy (The Layered Architecture)

The system is built on a strict inheritance model to ensure consistency and generic behavior.

- **Level 1: The Root (`Aras`)**
    - The foundational root class. Every framework component belongs to this root.
    - Provides core decorators: `@Aras.model_action`, `@Aras.computed_field`.
- **Level 2: The Core Abstractions**
    - `Model(Aras, Base)`: Data resource abstraction. Supports `__m2m__` and automated CRUD hooks. UI metadata is externalized to `View` classes.
    - `View(Aras)`: UI metadata and layout configuration. Allows defining `layout` (Section-based grouping) and field overrides independently of models.
    - `App(Aras)`: Application module abstraction. Supports `parent_name` for hierarchical organization.
    - `Manager(Aras)`: Orchestration abstraction (Audit, Sync, Task, Health).
    - `Validation(Aras, BaseModel)`: Data validation abstraction.
    - `WidgetModel(Model)`: Dashboard widget registry.
- **Level 3: Specific Implementations**
    - `User(Model)`: Authentication resource.
    - `AppModel(Model)`: Metadata persistence for installed apps.
    - `ResourceModel(Model)`: Metadata persistence for tables.
    - `FieldModel(Model)`: Metadata persistence for fields.
    - `ERP(App)`: Pluggable business modules.

## 3. Modular File Map (Target Phase 1)

| File Path | Level | Class | Purpose |
| :--- | :--- | :--- | :--- |
| `api/core/base/aras.py` | 1 | `Aras` | The foundational root class. |
| `api/core/base/model.py` | 2 | `Model` | Generic CRUD, M2M, & Metadata logic. |
| `api/core/base/app.py` | 2 | `App` | Manifest & registration logic. |
| `api/core/base/validation.py`| 2 | `Validation` | Pydantic validation base. |
| `api/core/manager/manager.py`| 2 | `Manager` | App discovery & sync. |
| `api/core/lib/storage.py` | 2 | `Storage` | Standardized file storage service. |
| `api/core/logic/router_factory.py`| 2 | `Router` | Generic CRUD + Export/Import factory. |

## 4. Coding Standards & Documentation
- **One File, One Class**: Strict modularity.
- **Header Comments**: Every file/function must have:
    - **Purpose**: Short description.
    - **Context**: Related files/inheritance.
    - **Impact**: System-wide effect.
- Jangan hapus tetapi update (hapus hanya yang sudah tidak relevan):
  - Jika ada fix laporkan di fix.md
  - Jika ada feature laporkan di feature.md
  - Jika ada perubahan pada framework laporkan di aras.md

## 5. UI Standard Hooks & Contexts
Aras provides a unified developer experience via React Contexts:
- `useAras()`: Primary hook for `notify`, `confirm`, and `api` access.
- `LogicEvaluator`: Safe, AST-like engine for complex conditional UI visibility.
- `MultiSelectCombobox`: Standardized UI for Many-to-Many associations.
- `CommandPalette`: Global `CMD+K` search interface with heuristic type detection.
- `DynamicForm`: Metadata-driven forms with support for `Layouts`, `Lookups`, `Select`, `File`, `Workflow`, `M2M`, and `Child Tables`.
- `DashboardView`: Dynamic visualization engine with support for `Stat`, `List`, and `Chart` (Bar/Pie) widgets.

## 6. Verification & Testing
The framework has been verified through automated end-to-end tests and manual stability audits covering:
- **Metadata Sync**: Confirmed Code-to-DB mapping including bridge (M2M) links.
- **Auto-Audit**: Verified change capture via SQLAlchemy events.
- **Workflow**: Confirmed state machine transition logic and UI rendering.
- **Data Portability**: Verified CSV Export/Import across all resources.
- **System Health**: Verified `HealthIntegrityView` for monitoring framework internals.
- **FastAPI Lifespan**: Modernized startup/shutdown logic for robust orchestration.
- **Visualization Tier**: Verified SVG-based charting engine with dynamic aggregation.
- **Security Hardening**: All admin/dev endpoints require authentication. CORS fixed. Pydantic v2 compliant. Test suite in `tests/test_auth_security.py`.

## 7. Security & Configuration

### Environment Configuration
All runtime config is loaded from `.env` via `api/core/lib/settings.py` (`Settings` class). `settings.validate()` must be called before any framework imports in `main.py`.

| Env Var | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | — (required in prod) | JWT signing key |
| `ARAS_ADMIN_PASSWORD` | — (required in prod) | Bootstrap admin password |
| `DATABASE_URL` | `mysql+pymysql://root:@localhost/aras` | DB connection string |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed browser origins |
| `APP_NAME` | `Aras` | Application display name |
| `ARAS_MODE` | `production` | Set to `development` for debug mode |

### Auth Dependency Chain
```
require_admin  →  get_current_user  →  JWT decode  →  DB user lookup
                ↳ raises 403 if not admin
                              ↳ raises 401 if no/invalid token
```
`require_admin` is defined in `api/core/auth/service.py` — single source of truth.

### RBAC Pattern
- `RBAC.has_permission(db, user, resource, action)` — single permission check
- `RBAC.get_readable_resources(db, user)` — bulk read of all resources user can READ (use before loops to avoid N+1)

---

## 8. App & Model Pattern (Quick Reference)

```python
# api/apps/myapp/models.py
from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from core import Aras

class MyModel(Aras.Model):
    __tablename__ = "myapp_items"       # REQUIRED: {app}_{table}
    __searchable_fields__ = ["name"]
    __display_fields__ = ("name",)
    __features__ = ["audit"]            # optional

    name: Mapped[str] = mapped_column(String(200))
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
```

```python
# api/apps/myapp/app.py
from core import Aras
from .models import MyModel
from . import views as _views  # noqa: triggers View registration

class MyModule(Aras.App):
    app_name = "myapp"
    app_label = "My App"
    icon = "Package"
    models = [MyModel]
```

```python
# api/apps/myapp/views.py  — only needed to override auto-derived title or add layout
from core import Aras
from .models import MyModel

class MyModelView(Aras.View):
    model = MyModel
    title = "My Items"   # omit if auto-derived class name is acceptable
```

Auto-generated endpoints for `myapp` / `myapp_items`:
- `GET/POST /api/v1/myapp/myapp_items`
- `GET/PUT/DELETE /api/v1/myapp/myapp_items/{id}`
- `GET /api/v1/metadata/myapp_items`

After any model/app change: `cd api && python manage.py sync`

---

## 9. API Endpoint Conventions (Refined May 2026)

The framework uses hierarchical, hyphenated paths for both UI navigation and API consistency.

| Pattern | Example |
|---|---|
| Hierarchical CRUD | `/api/v1/erp/accounting/accounts` |
| Deep Hierarchical CRUD| `/api/v1/erp/accounting/sales-invoices` |
| Auth token (form-encoded) | `POST /api/v1/auth/token` |
| Metadata | `GET /api/v1/metadata/erp/accounting/accounts` |
| Sidebar | `GET /api/v1/sidebar` |
| App Menu | `GET /api/v1/app-menu/erp/accounting` |

### URL Path Generation Logic
1.  **Hyphenation:** All underscores (`_`) in table/app names are converted to hyphens (`-`) for URL paths.
2.  **Prefix Stripping:** Current app and parent app prefixes are stripped from the model name for the last segment of the path.
    -   Example: App `erp_accounting` (parent `erp`), Model `erp_accounting_accounts` → `/erp/accounting/accounts`.
3.  **UI Redirection:** The frontend utilizes a `SmartDispatcher` to resolve these paths into either an `AppHome` (for 1 or 2 segments that match an app) or a `DynamicView` (for resource lists/forms).

Login (for scripts/tools):
```python
res = requests.post("http://localhost:8000/api/v1/auth/token",
                    data={"username": "admin", "password": "admin"})
token = res.json()["access_token"]
```

---

## 10. Multi-Agent Workflow (docs/handoff.md)

Claude writes a **short task spec** to `docs/handoff.md`, then Gemini (backend) and GPT-4.5 (frontend) implement it via `tools/multi_agent.py`. Claude never sees agent responses — they write files directly to disk.

### Handoff spec format (keep it SHORT — agents know the framework via backstory)

```markdown
## Context
One sentence: what this does and why.

## Backend Tasks
- ACTION `path/to/file.py` — intent + key fields/columns only
- ACTION `path/to/file2.py` — what to add/change

## Frontend Tasks
- ACTION `ui/src/views/Foo.tsx` — what to add/change
```

Actions: `NEW FILE`, `UPDATE`, `DELETE`

### Run commands
```bash
python tools/multi_agent.py               # full run (Gemini backend + GPT-4.5 frontend)
python tools/multi_agent.py --backend-only
python tools/multi_agent.py --frontend-only
```

### Completed runs are persisted to `dev_handoff_runs` table
Viewable at `/dev` → "Handoff Runs" tab. Fields: feature, mode, status, prompt_md, token counts.

---
**Status**: Stable, secure, Pydantic v2 compliant. Ready for app development.


---
## Framework Change: Hierarchical Application Architecture (2026-05-15)
- [Gemini CLI] `Aras.App` base class now supports `parent_name` attribute for building application hierarchies.
- [Gemini CLI] `AppModel` and `SyncManager` updated to persist and synchronize the parent-child relationships.
- [Gemini CLI] Recursive sidebar rendering implemented in React frontend, supporting visual indentation for sub-apps.
- [Gemini CLI] `AppHome` view enhanced to display sub-apps as interactive module tiles, improving navigation for complex suites.
- [Gemini CLI] Refactored ERP from a monolithic app into a hierarchical structure with six specialized sub-apps (`erp_accounting`, `erp_stock`, etc.) nested under a main `erp` shell.

---
## Framework Change: Section-Based Layouts & Default Analytics (2026-05-15)
- [Gemini CLI] Enhanced `DynamicForm` and `UIGenerator` to support section-based grouping of fields via the `__layout__` model attribute.
- [Gemini CLI] Core ERP models (SalesInvoice, JournalEntry, Product) updated with logical section definitions (e.g., 'Header', 'Financials') for better UI aesthetics.
- [Gemini CLI] `SyncManager.seed_widgets` now automatically populates the dashboard with default ERP analytics (Total Products, Recent Movements, etc.) on first sync.
- [Gemini CLI] Migrated automatic invoice recalculation logic (subtotal/tax/total) from legacy codebase into the new `SalesInvoice` model using framework hooks.

---
## Framework Change: Change Logging Rule + Manual Log Command (2026-05-14)
  - [Claude Code] dev_handoff_runs table: added author, notes columns; mode field now covers manual/claude-direct/human-direct

---
## Framework Change: Rate Limiting, Hooks, Batch API, WebSocket, Field Validation (2026-05-14)
- [Claude Sonnet 4.6] `RateLimiterMiddleware` added to `main.py` — all routes protected; auth endpoints throttled to 10/60s
- [Claude Sonnet 4.6] `@Aras.on_create`, `@Aras.on_update`, `@Aras.on_delete` decorators added to `Aras` base class; `Model._fire_hooks()` dispatches from `save()` and `delete_self()`
- [Claude Sonnet 4.6] `Field()` gains `min_length`, `max_length`, `min_value`, `max_value`, `pattern` — RouterFactory auto-wires them into Pydantic schemas
- [Claude Sonnet 4.6] `POST /batch` endpoint auto-generated by RouterFactory for all models (up to 100 mixed ops)
- [Claude Sonnet 4.6] Soft-delete models get `/deleted` (GET) and `/{id}/restore` (POST) auto-generated by RouterFactory
- [Claude Sonnet 4.6] `core/api/websocket.py` — WebSocket router at `/api/v1/ws?channel=`; `broadcast_sync()` for sync callers

---
## Framework Change: AI Direct Log Rule (2026-05-14)
- [Claude Sonnet 4.6] CLAUDE.md updated — all AIs working directly must append entries to `docs/feature.md`, `docs/fix.md`, and/or `docs/aras.md` after each task, with `[LLM Name]` on every bullet


---
## Framework Change: Dashboard Drag-to-Rearrange + Audit Log Timeline View — revision (2026-05-14)
  - [Gemini] Integrated widget order persistence into existing `DashboardLayoutModel` management.


---
## Framework Change: App Navigation Restructure — have_home + Topbar App Menu — revision (2026-05-14)
  - [Gemini] Updated `App` base class to support `have_home` configuration and enhanced `get_sidebar_data` response to include this new property.
  - [Codex/GPT-5.5] Added have_home support to SidebarItem and app-menu API consumption in layout views


---
## Framework Change: Primitives for Multi-Tenancy, Choices, Composite Uniqueness, and Workflow Hooks (2026-05-15)
- [Claude Opus 4.7] `__unique_together__: list[tuple[str,...]]` on a `Model` is materialized as composite `UniqueConstraint(...)` named `uq_{tablename}_{cols}` during `Model.__init_subclass__`.
- [Claude Opus 4.7] `info={"choices": [...]}` on a column is now first-class: `UIGenerator` emits `{type: "select", options: [...]}`; `RouterFactory` narrows the auto-generated Pydantic field to `Literal[*choices]` (server-side rejection of bad values).
- [Claude Opus 4.7] `__scoped_by__ = [(col_name, fk_table), ...]` declares tenant/company/workspace scoping. `TraitInjector._inject_scoped` auto-creates the FK columns (NOT NULL, indexed, `form_hidden`). `RouterFactory` applies `WHERE col = request.state.scope[col]` to list/get/update/patch and auto-injects scope on writes. The `scope` claim is carried in the JWT and resolved into `request.state.scope` by `get_current_user`. `POST /api/v1/auth/switch-scope` re-issues a token with a new scope.
- [Claude Opus 4.7] `is_active` is no longer a baseline column. Add `__features__ = ["activatable"]` to opt in. `_q(active_only=True)` is gated on `hasattr(cls, "is_active")`. Use `info={"form_hidden": True}` to exclude any column from auto-form rendering (still visible in API/detail). Existing registry models (`Role`, `Permission`, `User`, `AppModel`, `ResourceModel`, `FieldModel`) opt in explicitly.
- [Claude Opus 4.7] `@Aras.on_transition(model=Cls, from_="Draft", to="Posted")` registers a workflow callback that `WorkflowManager.trigger_action` fires after the status change. Callback signature: `(db, item, user, transition) -> None`. Failure rolls back the status change.
- [Claude Opus 4.7] `manage.py sync` now runs `auto_migrate` before the `SyncManager` queries the registry, so new framework columns (e.g. `aras_resources.scoped_by`) are present in time.

## Framework Change: Three-Layer Class Inheritance Contract (2026-05-15)

A concrete `Model` subclass MUST inherit from at most one Level-3a abstract base. `Model.__init_subclass__` validates this and raises `TypeError` on diamond inheritance.

```
Level 1   Aras                  (root — decorators)
Level 2   Aras.Model            (CRUD, metadata, traits)         — __abstract__ = True
Level 3a  App abstract mixins   (DocumentBase | LineItemBase | MasterDataBase | ConfigBase)
                                                                 — __abstract__ = True, no __tablename__
Level 3b  Concrete model        (SalesInvoice, StockProduct, ...) — exactly one __tablename__
```

Rules:
1. A concrete model picks ONE Level-3a base (`DocumentBase` OR `LineItemBase`, never both).
2. Level-3a bases set `__abstract__ = True` and have no `__tablename__`.
3. `__features__`, `__scoped_by__`, `__unique_together__` on the concrete class are MERGED with values from the MRO (deduped, child wins on conflict). UI metadata (labels, layouts, titles) MUST live in `View` classes — never on models.

Shared ERP bases live in `api/apps/erp/base/`:

| Base              | Features                                  | Use for                                               |
|-------------------|-------------------------------------------|-------------------------------------------------------|
| `DocumentBase`    | audit, workflow, scoped (company_id)      | Invoices, Orders, Payments, Movements                 |
| `LineItemBase`    | audit                                     | InvoiceLine, JournalLine, OrderLine, MovementLine     |
| `MasterDataBase`  | audit, activatable, scoped (company_id)   | Product, Customer, Supplier, Account                  |
| `ConfigBase`      | audit, activatable                        | Currency, Charge, Uom, ProductCategory (global)       |

Form-simplification matrix (codified here):

| Table type                 | `activatable`? | Status mechanism                |
|----------------------------|----------------|---------------------------------|
| Master data                | yes            | disable instead of delete       |
| Configuration              | yes            | disable instead of delete       |
| Documents                  | no             | `__features__ = ["workflow"]`   |
| Line items                 | no             | cascade with parent             |
| Pivot / M2M bridge         | no             | existence = membership          |
| Logs / immutable history   | no             | immutable by design             |

ERP module skeleton (Part B): Unified `erp` application registered under `api/apps/erp/` with sub-packages for `config`, `stock`, `accounting`, `crm`, `supplier`, and `pos`. Models are organized within these sub-packages and registered centrally in `ERP`. Table naming: strict `erp_<module>_<table>`.

## Framework Change: Unified Modular ERP Application (2026-05-15)
- [Gemini CLI] Consolidated six separate ERP apps into a single `erp` app in `api/apps/erp/`.
- [Gemini CLI] Implemented sub-package structure (`erp/config`, `erp/stock`, etc.) for better organization of the unified ERP suite.
- [Gemini CLI] Centralized model registration in `api/apps/erp/app.py`.

## Framework Change: ERP Financial Logic & Charge Framework (2026-05-15)
- [Gemini CLI] **Automated Posting Service**: Introduced `InvoicePostingService` in `accounting/services/posting.py` to handle the conversion of invoices into GL Journal Entries.
- [Gemini CLI] **Dynamic Recalculation**: Document models (`SalesOrder`, `SalesInvoice`, etc.) now utilize `Aras.on_create/update` hooks for automatic subtotal and charge recalculation.
- [Gemini CLI] **Charge Metadata Integration**: `Charge` models in `config` are now first-class citizens used for dynamic tax and fee calculations across all document types.
- [Gemini CLI] **POS Terminal Architecture**: Added `PosTerminal` as a configuration layer to override global stock/pricing settings for retail operations.

---
## Framework Change: Advanced Navigation & Hierarchical Menus (2026-05-15)
- [Gemini CLI] **Dual-Axis Navigation**: Sidebar is now reserved for global Application links, while Topbar handles App-specific navigation.
- [Gemini CLI] **Hierarchical Topbar**: Implemented support for nested grouping in the topbar via `menu_groups`.
- [Gemini CLI] **Smart Filtering**: Child tables (inheriting from `LineItemBase` or using `__parent__`) are automatically hidden from menus to reduce clutter.
- [Gemini CLI] **Tile-Based AppHome**: Enhanced the application landing page to show structured tiles based on the menu configuration.

---
## Framework Change: ERP Module Consolidation (2026-05-15)
- [Gemini CLI] **Config Module Expansion**: `erp_config` now serves as the unified hub for all system-wide settings, including Finance (Payment Modes), Standards (UOMs), and System Tools (Printing/Reporting).
- [Gemini CLI] **Module Purge**: The `erp_main` (System Tools) module has been deprecated and its resources migrated to `erp_config`.
- [Gemini CLI] **Relational Refactoring**: Standardized cross-module references to ensure that core configuration tables (like Payment Modes) are accessed via the Config registry even from within operational modules like POS or Accounting.

---
## Framework Change: Scoping Inheritance & Dynamic Attributes (2026-05-15)
- [Gemini CLI] `Model.__init_subclass__` now supports `__scoped_by__ = None` to explicitly stop feature/scope inheritance from abstract parents.
- [Gemini CLI] `TraitInjector` now injects columns into the class `__dict__` as well as the `__table__`, ensuring they are visible to the SQLAlchemy Mapper.
- [Gemini CLI] `manage.py seed` enhanced with `apps.discovery` and improved cross-company data isolation.

---
## Framework Change: UI Refactoring & Enhanced Customization (2026-05-15)
- [Gemini CLI] **Generic List Toolbar Component**: Extracted the toolbar logic from `ListView` into a standalone `ListToolbar` component. Integrated into `ListView` and `InlineChildTable` for consistent UX and feature parity (Search, Column Visibility) across all list views.
- [Gemini CLI] **Series Renaming**: Renamed `NamingSeries` to `Series` throughout the framework (file, class, managers, views) and updated the route registration pattern.
- [Gemini CLI] **GUI-Based Form Customization**: Added a "Customize" button to `DynamicForm` that allows editing `default_value` and `series` overrides for any field via `FieldModel` registry.
- [Gemini CLI] **Automatic Sequential ID Generation**: Implemented a series generation hook in `Model.save` that automatically populates fields with `series` metadata on record creation using `NamingManager`.
- [Gemini CLI] **Metadata Default Injection**: Updated `DynamicForm` initialization to prioritize `default_value` and `series` metadata from the `FieldModel` registry.

---
## Framework Change: View Auto-Generation & __title__ Rule Enforcement (2026-05-16)
- [Claude Sonnet 4.6] `View.__init_subclass__` now auto-derives `title` from model class name when not explicitly set — strips "Model"/"View" suffix, inserts spaces on CamelCase boundaries (`HandoffRun` → `"Handoff Run"`)
- [Claude Sonnet 4.6] `View._auto_register(model_cls)` classmethod added — ensures every model has a View entry on demand (creates minimal auto-View if none exists); used by `App.get_menu_structure()` and `RouterFactory`
- [Claude Sonnet 4.6] `App.get_menu_structure()` now resolves all menu labels via `View._auto_register()` instead of reading `Model.__title__` — View title wins, auto-derived title as fallback
- [Claude Sonnet 4.6] `RouterFactory` OpenAPI tags now use `View._auto_register(model).title` — removed last `__title__` dependency from non-View code
- [Claude Sonnet 4.6] `__title__` removed from all model files: `AppModel`, `ResourceModel`, `FieldModel`, `LinkModel`, `ActivityLog`, `ArasSetting`, `User`, `HandoffRun`, `Note`
- [Claude Sonnet 4.6] `UserView` added to `core/registry/views.py` with explicit `title = "System Users"` — overrides auto-derived `"User"`
- [Claude Sonnet 4.6] Rule: models NEVER set `__title__`; explicit View subclass for custom title; no View needed for default auto-derived title


---
## Framework Change: Fase 0 Closeout + Fase 1 Foundation (Multi-Tenant Core) — revision (2026-05-16)
  - [Codex/GPT-5.5] Axios response interceptor now unwraps data and normalizes failed envelope responses


---
## Framework Change: Fase 0 Closeout + Fase 1 Foundation (Multi-Tenant Core) — revision (2026-05-16)
  - [Gemini] Standardized all successful API responses to a consistent `{success, data, message, error}` format. Added a global exception handler to normalize all error responses and prevent stack trace leaks. Exposed the new tenant subsystem via the `Aras` facade.


---
## Framework Change: ARP Neutral Rename — Organization model, neutral DB schema, profile system, POT rename, party consolidation — revision (2026-05-16)
  - [Codex/GPT-5.5] App wrapped with VocabularyProvider; generic metadata-driven form/list/navigation layers now consume vocabulary labels
