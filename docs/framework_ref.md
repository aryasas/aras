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
| `Aras.App` | App manifest base |
| `Aras.Manager` | Orchestration base (Audit, Sync, Workflow, Task, Health) |
| `Aras.View` | UI metadata config base |
| `Aras.Schema` | Pydantic validation base |
| `Aras.Service` | Stateless logic base |
| `Aras.Router` | API routing base |
| `Aras.Auth` | Security/authorization base |
| `Aras.Validation` | Pydantic DTO base |
| `Aras.Field` | SQLAlchemy column wrapper |

**Level 2.5 — Tiered Core** (prevents circular imports):
| Tier | Path | Rule |
|---|---|---|
| Tier 0 `lib` | `api/core/lib/` | ZERO framework dependencies |
| Tier 1 `logic` | `api/core/logic/` | depends on lib + base only |
| Tier 2 `api` | `api/core/api/` | depends on any lower tier |

**Level 3 — Registry** (`api/core/registry/`):
| Model | Table | Purpose |
|---|---|---|
| `AppModel` | `aras_apps` | installed app records |
| `ResourceModel` | `aras_resources` | table/model metadata |
| `FieldModel` | `aras_fields` | field-level UI overrides |
| `LinkModel` | `aras_links` | relationship metadata |
| `TranslationModel` | `aras_translations` | i18n label records |
| `WidgetModel` | `aras_widgets` | dashboard widget definitions |
| `DashboardLayoutModel` | `aras_dashboard_layouts` | user dashboard configs |
| `ActivityLog` | `aras_activity_logs` | audit trail |
| `Role` / `Permission` / `UserRole` | `aras_roles/permissions/user_roles` | RBAC |
| `ArasSetting` | `aras_settings` | global key-value settings |

---

## Unified Namespace
```python
from core import Aras
# Aras.Model, Aras.App, Aras.Manager, Aras.View, Aras.Schema
# Aras.AppModel, Aras.ResourceModel, Aras.FieldModel, etc.
# Aras.User, Aras.ArasSetting
# Aras.lib, Aras.logic, Aras.api, Aras.helper
# Aras.Manager.Sync, Aras.Manager.Audit, Aras.Manager.Workflow
# Aras.Base (DeclarativeBase), Aras.engine, Aras.get_db
# Aras.Router = RouterFactory.create_router
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
| `__title__` | str | human label for sidebar/UI |

**Auto-provided base columns** (never declare): `id`, `is_active`, `created_at`, `updated_at`, `created_by`, `updated_by`

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
| `/api/v1/auth/login` | POST | JWT login |

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

## Do NOT Re-read
- `api/core/base/aras.py` — Level 1 root, ~27 lines, static
- `api/core/aras.py` — unified facade, use table above
- `api/core/base/model.py` — use Model attributes table above
- `api/main.py` — use Startup Flow in `docs/aras.md`
- `aras-old/` — LEGACY, never read
