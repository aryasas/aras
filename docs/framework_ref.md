# Framework Reference (New Stack)

> FastAPI + SQLAlchemy 2.0 backend · React 19 + TypeScript frontend
> See `docs/aras.md` for full architecture, patterns, and examples.

---

## Architecture: Strict 3-Level Hierarchy

**Level 1 — Root** (`api/core/base/aras.py`):
- `Aras` — ultimate base class. Provides `@Aras.model_action` and `@Aras.computed_field`.

**Level 2 — Core Abstractions** (`api/core/base/`):
| Class | Purpose |
|---|---|
| `Aras.Model` | SQLAlchemy model base (CRUD, audit, M2M, workflow, layout) |
| `Aras.SoftModel` | `Model` subclass with soft-delete built-in |
| `Aras.App` | App manifest base. Supports `parent_name`, `have_home`, `menu_groups` |
| `Aras.Manager` | Orchestration — `Manager.Sync`, `Manager.Audit`, `Manager.Workflow` |
| `Aras.View` | UI metadata config base. Title auto-derived if not set. |
| `Aras.Schema` | Pydantic validation base |
| `Aras.Service` | Stateless logic base |
| `Aras.Router` | API routing factory (`RouterFactory.create_router`) |
| `Aras.Auth` | Security/authorization base |
| `Aras.Validation` | Pydantic DTO base |
| `Aras.Field` / `Aras.Column` | SQLAlchemy column wrapper with UI metadata (`choices`, `form_hidden`, etc.) |

**Level 2.5 — Tiered Core** (prevents circular imports):
| Tier | Path | Rule |
|---|---|---|
| Tier 0 `lib` | `api/core/lib/` | ZERO framework dependencies |
| Tier 1 `logic` | `api/core/logic/` | depends on lib + base only |
| Tier 2 `api` | `api/core/api/` | depends on any lower tier |

**Level 3 — Registry** (`api/core/registry/`):
| Class | Table | Purpose |
|---|---|---|
| `Aras.AppModel` | `aras_apps` | installed app records |
| `Aras.ResourceModel` | `aras_resources` | table/model metadata |
| `Aras.FieldModel` | `aras_fields` | field-level UI overrides |
| `Aras.LinkModel` | `aras_links` | relationship metadata |
| `Aras.TranslationModel` | `aras_translations` | i18n label records |
| `Aras.WidgetModel` | `aras_widgets` | dashboard widget definitions |
| `Aras.DashboardLayoutModel` | `aras_dashboard_layouts` | per-user dashboard configs |
| `Aras.ActivityLog` | `aras_activity_logs` | audit trail |
| `Aras.Role` / `Aras.Permission` / `Aras.UserRole` | `aras_roles/permissions/user_roles` | RBAC |
| `Aras.User` | `aras_users` | authentication |
| `Aras.ArasSetting` | `aras_settings` | global key-value settings |
| `Aras.HandlerRegistry` | — | workflow transition handler registry |

---

## Unified Namespace
```python
from core import Aras
# Level 2: Aras.Model, Aras.SoftModel, Aras.App, Aras.View, Aras.Schema
#          Aras.Service, Aras.Router, Aras.Auth, Aras.Validation
#          Aras.Field / Aras.Column
# Level 3: Aras.AppModel, Aras.ResourceModel, Aras.FieldModel, Aras.LinkModel
#          Aras.User, Aras.ArasSetting, Aras.ActivityLog, Aras.HandlerRegistry
#          Aras.Role, Aras.Permission, Aras.UserRole, Aras.WidgetModel
# Managers: Aras.Manager.Sync, Aras.Manager.Audit, Aras.Manager.Workflow
# DB:       Aras.Base, Aras.engine, Aras.get_db, Aras.db
# Util:     Aras.discover_apps, Aras.tenant, Aras.helper, Aras.lib, Aras.logic, Aras.api
# Routing:  Aras.Router = RouterFactory.create_router
```

---

## Model Class Attributes
| Attribute | Type | Purpose |
|---|---|---|
| `__tablename__` | str | REQUIRED. Format: `{app}_{table}` |
| `__features__` | list | `["audit"]`, `["audit", "workflow"]` |
| `__workflow__` | bool | enable workflow engine |
| `__transitions__` | list | `[{"from": "Draft", "to": "Confirmed", "label": "..."}]` |
| `__layout__` | list | `[{"title": "Section", "fields": [...]}]` for UI sections |
| `__m2m__` | dict | M2M relationship definitions |
| `__parent__` | str | tablename of parent model (child tables) |
| `__display_fields__` | tuple | fields used in search/choices display |
| `__searchable_fields__` | list | fields searched by global search |
| `__soft_delete__` | bool | enable soft delete |
| `__serialize_relations__` | dict | `{key: (rel_attr, rel_field)}` for `to_dict()` |

> **`__title__` is removed** — do NOT set it on models. Use a `View` subclass with `title = "..."` instead. Auto-derived from class name when no View exists.

**Auto-provided base columns** (never declare): `id`, `created_at`, `updated_at`, `created_by`, `updated_by`
**`is_active`** is NOT auto-provided — add `__features__ = ["activatable"]` to opt in.

---

## Key Logic Modules (`api/core/logic/`)
| File | Class/Function | Purpose |
|---|---|---|
| `router_factory.py` | `RouterFactory.create_router(model)` | generates full CRUD FastAPI router |
| `discovery.py` | `discover_apps(package_path)` | walks apps/, imports all, checks inheritance |
| `discovery.py` | `register_app_routes(app, prefix)` | mounts per-app CRUD routers |
| `ui_generator.py` | `UIGenerator.generate_metadata(model, db, lang)` | code → UI JSON (merged with DB overrides) |
| `auto_migrate.py` | `run(engine, metadata)` | safe SQLAlchemy schema migration (no files) |
| `integrity_checker.py` | `IntegrityChecker.check_module(module)` | enforces Aras inheritance on all classes |
| `permissions.py` | `check_permissions(...)` | RBAC enforcement |
| `model_actions.py` | `action(...)` | `@Aras.model_action` decorator impl |
| `trait_injector.py` | `TraitInjector.inject(cls)` | injects audit/workflow features into models |
| `workflow.py` | — | state machine logic |
| `installer.py` | — | YAML/JSON/ZIP app bundle installer |

## Key Manager Classes (`api/core/manager/`)
| File | Class | Purpose |
|---|---|---|
| `sync_manager.py` | `SyncManager.sync_all(db)` | code-to-DB metadata sync |
| `audit_manager.py` | `AuditManager.register_listeners()` | SQLAlchemy event-based field logging |
| `workflow_manager.py` | `WorkflowManager` | state machine orchestration |
| `task_manager.py` | `TaskManager` | Celery background task queue |
| `health_manager.py` | `HealthManager` | system health checks |

---

## API Endpoints Pattern
All routes prefixed `/api/v1/`.

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/{table}` | GET | List with pagination & filtering |
| `/api/v1/{table}` | POST | Create |
| `/api/v1/{table}/{id}` | GET/PUT/DELETE | Retrieve/Update/Delete |
| `/api/v1/{app}/{table}/{id}/action/{name}` | POST | Custom model action |
| `/api/v1/search` | POST | Global multi-resource search |
| `/api/v1/metadata/{resource}` | GET | UI metadata for forms/tables |
| `/api/v1/dashboard` | GET | Dashboard widgets & layout |
| `/api/v1/sidebar` | GET | Dynamic sidebar data |
| `/api/v1/files/...` | * | File upload/download |
| `/api/v1/workflow/...` | * | Workflow transitions |
| `/api/v1/auth/token` | POST | JWT login (form-encoded: `username`, `password`) |
| `/api/v1/tenants` | GET/POST | List / provision tenants (admin only) |
| `/api/v1/tenants/{id}/seed` | POST | Seed a provisioned tenant (admin only) |
| `/api/v1/tenants/{id}` | DELETE | Deprovision tenant (admin only) |

---

## Frontend Architecture (`ui/`)

**Stack**: React 19.2.6 + TypeScript + Vite 8 + TailwindCSS 4 + Zustand + React Query + Axios

### Key Directories
```
ui/src/
├── App.tsx                    # Router + global error/alert handlers
├── main.tsx                   # Entry: QueryClient, Auth/UI providers
├── aras-core/
│   ├── components/            # Core widgets
│   ├── contexts/              # ConfirmContext, NotificationContext
│   ├── hooks/useAras.ts       # PRIMARY hook: notify, confirm, api
│   └── services/              # FormattingService, MetadataService, SchemaRegistry
├── layouts/                   # MainLayout + Sidebar + Header
├── views/                     # 14 page views
├── store/                     # authStore, uiStore
└── lib/                       # api.ts (Axios), LogicEvaluator.ts
```

### Core Components (`ui/src/aras-core/components/`)
| Component | Purpose |
|---|---|
| `DynamicForm.tsx` | metadata-driven form (layout, lookup, file, workflow, M2M, child tables) |
| `DynamicTable.tsx` | metadata-driven table |
| `ListView.tsx` | list view with search, filter, pagination, import/export |
| `DashboardView.tsx` | widget dashboard (stat, list, chart bar/pie) |
| `CommandPalette.tsx` | CMD+K global search overlay |
| `MultiSelectCombobox.tsx` | M2M relationship selector |
| `ImportMapping.tsx` | CSV column→field mapping UI |
| `Combobox.tsx` | single select with search |
| `FileField.tsx` | file upload field |
| `SidePanel.tsx` | slide-in panel for quick views |
| `GlobalDialog.tsx` | modal dialog |

### Services (`ui/src/aras-core/services/`)
| Service | Purpose |
|---|---|
| `FormattingService.ts` | date/number formatting from `ArasSetting` |
| `MetadataService.ts` | caches resource metadata per session |
| `SchemaRegistry.tsx` | plugin registry for custom field widgets |

### Frontend Routes (`App.tsx`)
| Path | View |
|---|---|
| `/login`, `/forgot-password`, `/reset-password` | Auth views |
| `/` or `/dashboard` | HomeView |
| `/settings`, `/settings/global`, `/settings/audit`, `/settings/rbac` | Settings views |
| `/dev`, `/dev/health`, `/dev/routes`, `/dev/table/:app/:model` | Dev views |
| `/apps` | AppManagerView |
| `/profile` | ProfileView |
| `/:app/:model` | DynamicView (list) |
| `/:app/:model/:id` | DynamicView (form) |

### Primary Hook
```typescript
const { notify, confirm, api, appName, formatDate, formatCurrency } = useAras()
// notify('Message', 'success' | 'error' | 'warning')
// confirm(options: ConfirmOptions) → Promise<boolean>
// api — Axios instance (baseURL: /api/v1)
// appName — first URL path segment (e.g. 'erp'), from useLocation()
// formatDate(isoString) → locale date string
// formatCurrency(amount) → USD currency string
```

### State Stores
- `authStore`: `token`, `user`, `setToken`, `logout`
- `uiStore`: `showAlert`, `showConfirm`, `showError`

---

## manage.py Commands (run from `api/`)

| Command | Purpose |
|---|---|
| `python manage.py sync` | Discover apps, create/migrate tables, sync metadata — **run after every model/app change** |
| `python manage.py seed --company-id 1` | Seed CoA, reports, initial data. Add `--demo` for demo data. |
| `python manage.py discover` | List all discovered apps and labels |
| `python manage.py check` | Run health + integrity checks |
| `python manage.py install <file.yaml>` | Install app from YAML/JSON/ZIP bundle |
| `python manage.py uninstall <name>` | Remove app from filesystem + DB |
| `python manage.py activate <name>` | Activate app in registry |
| `python manage.py deactivate <name>` | Deactivate app in registry |
| `python manage.py tenant provision <id>` | Provision a new tenant PostgreSQL DB |
| `python manage.py tenant seed <id>` | Seed basic data into a tenant DB |
| `python manage.py tenant list` | List all registered tenants |
| `python manage.py tenant deprovision <id>` | Soft-delete a tenant DB |

---

## App Patterns

### Minimal App
```python
# models.py
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from core import Aras

class MyModel(Aras.Model):
    __tablename__ = "myapp_items"
    __searchable_fields__ = ["name"]
    __features__ = ["audit"]
    name: Mapped[str] = mapped_column(String(200))
```

```python
# app.py
from core import Aras
from .models import MyModel
from . import views as _views  # noqa

class MyApp(Aras.App):
    app_name = "myapp"
    app_label = "My App"
    icon = "Package"
    models = [MyModel]
```

```python
# views.py — only when overriding title or adding layout
from core import Aras
from .models import MyModel

class MyModelView(Aras.View):
    model = MyModel
    title = "My Items"
```

### File Structure

Flat app:
```
api/apps/myapp/
├── __init__.py
├── app.py        — Aras.App subclass, lists models
├── models.py     — Aras.Model subclasses
└── views.py      — only if overriding title/layout
```

App with modules (ERP pattern):
```
api/apps/myapp/
├── __init__.py
├── app.py                — parent App (have_home=True)
├── base/                 — optional Level-3a abstract bases
│   ├── document.py
│   └── master_data.py
├── accounting/           — sub-module
│   ├── __init__.py
│   ├── app.py            — subclass, parent_name="myapp"
│   ├── models.py
│   ├── views.py
│   └── services/         — stateless logic (Aras.Service)
└── stock/
    ├── __init__.py
    ├── app.py
    ├── models.py
    └── services/
```

Rules: `services/` = stateless only. `routers/` = custom endpoints; register via `App.routers = [router]`. Never put business logic in `models.py` or `views.py`.

### Multi-file Models
```python
from core.logic.discovery import autodiscover_models

class MyApp(Aras.App):
    app_name = "myapp"
    models = autodiscover_models(__name__, ["models", "models_extra"])
```

### menu_groups (topbar navigation)
```python
class MyApp(Aras.App):
    app_name = "myapp"
    have_home = True
    menu_groups = [
        {"label": "Master", "icon": "Database", "models": ["myapp_items"]},
        {"label": "Operations", "icon": "Truck", "models": ["myapp_orders"]},
    ]
```

---

## ERP Sub-Apps (`api/apps/erp/`)

`ERP` base class owns `SavedFilter` + `saved_filter_router`. Sub-apps inherit `ERP` — auto-sets `parent_name = "erp"`, `app_type = "module"`.

| Dir | `app_name` | Key models |
|---|---|---|
| `accounting` | `erp_accounting` | Account, SalesInvoice, JournalEntry, GRN |
| `stock` | `erp_stock` | Product, StockMovement, Warehouse |
| `config` | `erp_config` | Currency, Uom, Charge, ModeOfPayment, PrintTemplate |
| `crm` | `erp_crm` | Lead, Pipeline, Stage, Activity |
| `hr` | `hr` | Department, Position, Employee |
| `party` | `party` | Party, Contact |
| `asset` | `asset` | AssetCategory, Asset |
| `pot` | `pot` | PotTerminal, PotSession, PotOrder, PotOrderLine |
| `report` | `erp_report` | Report |

ERP abstract bases (`api/apps/erp/base/`):

| Base | Features | Use for |
|---|---|---|
| `DocumentBase` | audit, workflow, scoped (company_id) | Invoices, Orders, Movements |
| `LineItemBase` | audit | Invoice/Order/Journal lines |
| `MasterDataBase` | audit, activatable, scoped (company_id) | Product, Customer, Account |
| `ConfigBase` | audit, activatable | Currency, Uom, Charge (global) |

---

## Do NOT Re-read
- `api/core/base/aras.py` — Level 1 root, ~27 lines, static
- `api/core/aras.py` — unified facade, use table above
- `api/core/base/model.py` — use Model attributes table above
- `api/main.py` — use Startup Flow in `docs/aras.md`
- `aras-old/` — LEGACY, never read
