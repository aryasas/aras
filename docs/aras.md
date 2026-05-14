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

## 8. App & Model Pattern (Quick Reference)

```python
# api/apps/myapp/models.py
from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from core import Aras

class MyModel(Aras.Model):
    __tablename__ = "myapp_items"       # REQUIRED: {app}_{table}
    __title__ = "My Items"
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

class MyApp(Aras.App):
    app_name = "myapp"
    app_label = "My App"
    icon = "Package"
    models = [MyModel]
```

Auto-generated endpoints for `myapp` / `myapp_items`:
- `GET/POST /api/v1/myapp/myapp_items`
- `GET/PUT/DELETE /api/v1/myapp/myapp_items/{id}`
- `GET /api/v1/metadata/myapp_items`

After any model/app change: `cd api && python manage.py sync`

---

## 9. API Endpoint Conventions

| Pattern | Example |
|---|---|
| App-scoped CRUD | `/api/v1/{app}/{tablename}` |
| Auth token (form-encoded) | `POST /api/v1/auth/token` with `username=` + `password=` |
| Dev tools | `GET /api/v1/dev/info`, `GET /api/v1/dev/stats` |
| Metadata | `GET /api/v1/metadata/{tablename}` |
| Global search | `POST /api/v1/search` |
| Sidebar | `GET /api/v1/sidebar` |

Auth header: `Authorization: Bearer <token>`

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
