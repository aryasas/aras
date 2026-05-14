# Aras Framework: Technical Report & Architecture Guide

## 1. System Overview
Aras is a metadata-centric application framework designed for extreme developer productivity. It follows a **Code-First, GUI-Override** philosophy where the database acts as a registry for code-defined models.

## 2. Inheritance Hierarchy (The Layered Architecture)

The system is built on a strict inheritance model to ensure consistency and generic behavior.

- **Level 1: The Root (`Aras`)**
    - The foundational root class. Every framework component belongs to this root.
    - Provides core decorators: `@Aras.model_action`, `@Aras.computed_field`.
- **Level 2: The Core Abstractions**
    - `Model(Aras, Base)`: Data resource abstraction. Supports `__layout__`, `__m2m__`, and automated CRUD hooks.
    - `App(Aras)`: Application module abstraction.
    - `Manager(Aras)`: Orchestration abstraction (Audit, Sync, Task).
    - `Validation(Aras, BaseModel)`: Data validation abstraction.
    - `WidgetModel(Model)`: Dashboard widget registry.
- **Level 3: Specific Implementations**
    - `User(Model)`: Authentication resource.
    - `AppModel(Model)`: Metadata persistence for installed apps.
    - `ResourceModel(Model)`: Metadata persistence for tables.
    - `ErpApp(App)`: Pluggable business modules.

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
**Status**: Stable, secure, Pydantic v2 compliant. Ready for app development.
