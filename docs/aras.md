### Shortcut Commands


| Command | Meaning |
|---|---|
| `mha` | Write `docs/handoff.md` spec only. Print: `python tools/multi_agent.py` |
| `mha be` | Same, print: `python tools/multi_agent.py --backend-only` |
| `mha fe` | Same, print: `python tools/multi_agent.py --frontend-only` |
| `mha test` | Print: `python tools/multi_agent.py --test 'hello'` |
| `rhf` | Review `docs/handoff.md` Agent Reports — verify files exist, append `## Claude Review` block with `APPROVED` or `NEEDS-FIX`. If NEEDS-FIX add `## Revision Tasks`. Run `cd api && python manage.py sync` if models changed. |
| `mhl` | Run manual change log (see Change Logging below) |
| `cmp` | Inspect project — review code, UI (ease, position, aesthetic), find repeatables to refactor. Report what to add/improve before building new apps. |
| `ggc` | Give git commit command text for all changes — do NOT execute, user runs it |
| `updd` | Update `docs/feature.md` (add only) and `docs/aras.md` if framework changed |
| `dde` | Don't do edit — no changes whatsoever |
| `rrc` | Re-read CLAUDE.md rules 1-3 before anything else |
dont run multi_agent directly, i will run it

# Aras Framework — Architecture Reference

> FastAPI + SQLAlchemy 2.0 backend · React 19 + TypeScript frontend
> **Detail tables** (classes, attributes, endpoints, components, file structure): `docs/framework_ref.md`
> **Reading rule**: Never full-read `framework_ref.md` — use only the exact line range shown in each pointer below.
> **Sync rule**: If line numbers in `aras.md` or `framework_ref.md` shift due to edits, update ALL affected `→ framework_ref.md L…` pointers in BOTH files immediately.

Aras is a general-purpose, metadata-driven application framework — not an ERP. It provides a code-first model registry, auto-generated CRUD APIs, metadata-driven UI, RBAC, workflow engine, multi-tenancy, and a modular app system where each app is an independently installable unit. An app can contain sub-modules (via `parent_name`), each owning its own models and routes — ERP uses this to organize Accounting, Stock, CRM, and others as modules under one app. Any other standalone system can be built the same way: a hospital patient registry, a school management system, a property rental platform — each as its own app with whatever modules it needs.

---

## Architecture

**Code-First, GUI-Override**: models defined in code; DB acts as metadata registry.

### Inheritance Layers
```
Level 1   Aras                  — root; @model_action, @computed_field, @on_create/update/delete, @on_transition
Level 2   Model / View / App / Manager / Schema / Service / Router / Auth / Validation / Field
Level 2.5 Tiered core           — lib (no deps) → logic (lib+base) → api (any lower)
Level 3a  App abstract bases    — optional, app-defined; e.g. ERP uses DocumentBase | LineItemBase | MasterDataBase | ConfigBase
                                   (__abstract__ = True, no __tablename__) — concrete model inherits ONE of these
Level 3b  Concrete models       — exactly one __tablename__, inherits ONE Level-3a base (or Aras.Model directly)
Level 3c  Registry models       — AppModel, ResourceModel, FieldModel, User, Role, … (aras_* tables)
```

All classes accessed via unified namespace — `from core import Aras`. → `framework_ref.md` L8–66 (Architecture, Unified Namespace)

### App Discovery & Startup Flow

1. `api/apps/` is scanned at startup — any `Aras.App` subclass found is auto-registered.
2. `python manage.py sync` must be run after any model/app change — writes to `aras_*` registry tables and runs `auto_migrate`.
3. Routes are auto-mounted per app via `RouterFactory` — no manual router wiring needed.
4. Apps are isolated by `app_name`; sub-modules set `parent_name` to nest under a parent app.

Full `manage.py` command list: → `framework_ref.md` L211–227

---

## Model Rules

- `__tablename__` — REQUIRED, `{app_name}_{table}` (e.g. `erp_accounting_accounts`)
- `__features__` — `["audit"]`, `["audit", "workflow"]`, `["activatable"]`
- `__scoped_by__` — `[(col, fk_table)]` — auto-injects FK col + WHERE filter per JWT scope
- `__unique_together__` — `[("col_a", "col_b")]` — composite UniqueConstraint
- `info={"choices": [...]}` — emits select UI + narrows Pydantic field to `Literal[*choices]`
- `info={"form_hidden": True}` — hides from auto-form, still visible in API
- `__title__` is **removed** — use `View.title` instead
- `is_active` is NOT auto-provided — opt in via `__features__ = ["activatable"]`
- Auto-provided columns (never declare): `id`, `created_at`, `updated_at`, `created_by`, `updated_by`
- Full attribute list: → `framework_ref.md` L70–89

## View Rules

- Title auto-derived from model class name (strips "Model"/"View" suffix, splits CamelCase).
- Only write a View to override title, add layout, or customize fields.
- `View._auto_register(model_cls)` ensures every model has a View on demand.
- Import views in `app.py`: `from . import views as _views  # noqa`

---

## Development Mandates

1. Table naming: ALWAYS `{app_name}_{table}` (e.g. `erp_stock_products`, `erp_accounting_accounts`)
2. After changing `models.py` or `app.py`: run `python manage.py sync` from `api/`
3. One file, one class — strict modularity
4. Never run long-running servers as foreground
5. Run from `api/` dir; `sys.path` must include `api/`
6. Models contain ONLY data/schema — never `__title__`, `__icon__`, or display attributes
7. Views contain ALL UI metadata — title, icon, fields overrides, layout
8. Every folder must have `__init__.py` — discovery uses `pkgutil.walk_packages`

App patterns, file structure, `autodiscover_models`, `menu_groups`: → `framework_ref.md` L230–321

---

## API Conventions

All routes prefixed `/api/v1/`. Underscores → hyphens. App/parent prefixes stripped from last path segment.

Example: App `erp_accounting` (parent `erp`), model `erp_accounting_accounts` → `/api/v1/erp/accounting/accounts`

Full endpoint list: → `framework_ref.md` L118–137

---

## Security & Config

Config from `.env` via `api/core/lib/settings.py`. Key vars: `SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS`, `ARAS_MODE`.

Auth chain: `require_admin → get_current_user → JWT decode → DB lookup` (`api/core/auth/service.py`).

RBAC: `RBAC.has_permission(db, user, resource, action)` · `RBAC.get_readable_resources(db, user)`

Logic modules + Manager classes: → `framework_ref.md` L92–115

---

## ERP App (`api/apps/erp/`)

ERP is the built-in example app. It uses a parent+module structure: `erp` (parent) owns `SavedFilter` and `saved_filter_router`; all sub-modules (`erp_accounting`, `erp_stock`, etc.) inherit from `ERP` which auto-sets `parent_name = "erp"`. ERP abstract bases (`DocumentBase`, `LineItemBase`, `MasterDataBase`, `ConfigBase`) are defined in `api/apps/erp/base/` and are ERP-specific — not framework primitives.

Full sub-app and base tables: → `framework_ref.md` L325–349

---

## Field & View Load Pipeline

How a model field goes from Python definition to rendered UI input.

### Startup (once per server boot)
```
models.py       SQLAlchemy column defined (type, FK, info={...})
    ↓
sync_manager    UIGenerator.generate_metadata(model_cls)  — no DB session
                → reads model_cls.__table__.columns
                → detects FK → ui_type="lookup", target_resource resolved via App._registry
                → detects choices → ui_type="select"
                → detects _file/_image suffix → ui_type="file"/"image"
                → produces field_meta_map {name: {type, label, hidden, ...}}
    ↓
sync_manager    For each column: upsert FieldModel row into aras_fields (registry DB)
                • New column   → INSERT with code-derived defaults
                • Existing row → UPDATE only if is_override=False (GUI-set values are preserved)
    ↓
auto_migrate    ALTER TABLE ... ADD COLUMN for any column missing from live DB
                Priority: model → DB (never drops unless explicitly configured)
```

### Per-Request (metadata endpoint)
```
GET /api/v1/{app}/{resource}/metadata
    ↓
UIGenerator.generate_metadata(model_cls, db=session)
    ↓
    1. Load ResourceModel row → db_resource (title, layout JSON)
    2. Load all FieldModel rows for resource → db_fields {name: FieldModel}
    3. Walk model_cls.__table__.columns (source of truth for field list)
       For each column:
         • FK?          → ui_type="lookup", target_resource = resolved app path
         • choices?     → ui_type="select"
         • suffix?      → ui_type="file"/"image"
         • db_field exists and is_override=True → use DB label/type/hidden (GUI override wins)
         • else         → use code-derived value
    4. Append computed_fields (@Aras.computed_field decorated)
    5. Append child_table entries from Model._child_map
    6. Attach layout from db_resource.layout (JSON) — [] if none set
    ↓
Response: { resource, title, fields: [...], layout: [...], actions: [...], children: [...] }
```

### Frontend Rendering
```
DynamicForm mounts
    ↓
useEffect → MetadataService.get(resource) → GET .../metadata
    ↓
fields[]  → renderField() per field
            • type="lookup"      → Combobox with /search endpoint
            • type="select"      → <select> from options[]
            • type="child_table" → InlineChildTable component
            • type="boolean"     → Toggle
            • type="date"        → DatePicker
            • default            → <input type="text|number">
    ↓
layout[]  → if populated, fields grouped into sections or tabs
            • LayoutSection  { title, fields[] }        → card with header
            • LayoutGroup    { type:"tabs", tabs[] }    → tab bar, one panel visible
            • Empty layout   → all fields in single unsectioned card
```

### Override Priority (field metadata)
```
GUI edit (is_override=True)  >  View class definition  >  model column info={}  >  auto-detected defaults
```

### How to control field display
- **Hide from form only**: `info={"form_hidden": True}` — field still in API, hidden in UI form
- **Hide everywhere**: `info={"hidden": True}` — or set `is_hidden=True` via GUI
- **Custom label**: `info={"label": "My Label"}` — or set in GUI (becomes `is_override=True`)
- **Force UI type**: `info={"ui_type": "textarea"}` — overrides auto-detection
- **Read-only**: `info={"read_only": True}`
- **Layout/tabs**: set `ResourceModel.layout` via GUI or `python manage.py sync` with a View that sets `__layout__`

---

## UI Hooks & Components

Primary hook: `useAras()` → `{ notify, confirm, api, appName, formatDate, formatCurrency }`

Key components: `DynamicForm`, `ListView`, `DashboardView`, `CommandPalette`, `MultiSelectCombobox`

API responses: `{ success, data, message, error }` envelope

Full component/hook/route tables: → `framework_ref.md` L140–208

---

## Workflow & Agent Roles

### Agent Responsibilities
| Agent | Role | Tools |
|---|---|---|
| **Claude** | Orchestrator — writes `docs/handoff.md` spec, reviews output (`rhf`), direct fixes | Claude Code CLI |
| **Gemini** | Backend implementor — FastAPI, SQLAlchemy, services, migrations | Gemini CLI |
| **GPT-4.5 (Codex)** | Frontend implementor — React, TypeScript, UI components | Codex CLI |

Claude NEVER writes code when `mha` is used — spec only. Gemini/GPT implement from `docs/handoff.md`.

### Handoff Spec Format
```markdown
## Context
One sentence.

## Backend Tasks
- ACTION `path/to/file.py` — intent

## Frontend Tasks
- ACTION `ui/src/views/Foo.tsx` — intent
```

Actions: `NEW FILE`, `UPDATE`, `DELETE`. Keep specs SHORT — agents have this doc in context.

```bash
python tools/multi_agent.py               # full run
python tools/multi_agent.py --backend-only
python tools/multi_agent.py --frontend-only
```

Runs logged to `dev_handoff_runs` table, viewable at `/dev` → "Handoff Runs".


### Change Logging (MANDATORY for all AIs)

After any direct task, append to relevant docs **before** reporting done:

- **`docs/feature.md`** — new feature added:
  ```
  ## <Name> (<YYYY-MM-DD>)
  - [<LLM>] <what was added, one bullet per file>
  ```
- **`docs/fix.md`** — bug fixed:
  ```
  ## <Description> (<YYYY-MM-DD>)
  - [<LLM>] <what was fixed and where>
  ```
- **`docs/aras.md`** — framework itself changed:
  ```
  ## Framework Change: <Description> (<YYYY-MM-DD>)
  - [<LLM>] <what changed>
  ```

`<LLM>` = exact model name (e.g. `Claude Sonnet 4.6`, `Gemini 2.5 Flash`, `GPT-4.5`). Append only, never delete.

| Who | How |
|---|---|
| `multi_agent.py` | Automatic after each run |
| Any AI directly | Write docs above, then run `mhl` |
| Human directly | Run `mhl` with `author=human` |

### `mhl` Command
```
python tools/multi_agent.py --log-manual \
  feature='<name>' author='<AI or human>' mode='claude-direct' \
  files='<comma-separated>' features='<added or none>' fixes='<fixed or none>' \
  framework='<changes or none>' issues='<issues or none>'
```

### File Reading
To read ANY file: `<project_root>/tools/smart_read.sh <filepath>` — handles deduplication automatically.

### Do NOT Re-read
- `api/core/base/aras.py` — Level 1 root, ~27 lines, static
- `api/core/aras.py` — unified facade, use Unified Namespace table → `framework_ref.md` L54–66
- `api/core/base/model.py` — use Model attributes table → `framework_ref.md` L70–89
- `api/main.py` — use Startup Flow above (L29–34)
- `aras-old/` — LEGACY, never read
- `docs/framework_ref.md` — never full-read; use exact line ranges pointed from this file only

### Credentials
Login: `admin` / `admin`

---

## Hard Rules — Database

**Never use SQLite.** The only database is the single configured production DB (Postgres/MySQL via `DATABASE_URL`). SQLite `.db` files are never created, committed, or used — not for tests, not for development. Any `*.db` file in the repo should be deleted immediately.


---
## Framework Change: Plan.md Full Build Queue — Backend 0, C1–C3, Backend 3–4, U4, U13, U14, Backend 6, H1–H2, R4, R6, H4, Backend 5+7–14, P1–P5, R1, R5, Backend 9–10, U1, U5, U2–U3, U6, U11 (2026-05-17)
  - [Gemini] Introduced custom exception handling and standardized API response patterns.
  - [Gemini] Implemented M2M field population in `Model.paginate` and moved transaction commits to `RouterFactory` for atomicity.
  - [Gemini] Implemented child hydration in `RouterFactory` for `GET /{id}` endpoints.
  - [Gemini] Included `@Aras.computed_field` decorated fields in `ui_generator.py` metadata output.
  - [Gemini] Added `/aggregate` endpoint to `RouterFactory`.
  - [Gemini] Wrapped `@Aras.model_action` handlers in ERP with `response.ok(data=...)` and handled exceptions.
  - [Gemini] Replaced bare `except: pass` with `except Exception as e: logging.warning(...)` in `model.py`.
  - [Gemini] Audited and fixed layout sections in `pot/views.py` for missing/duplicate keys.
  - [Gemini] Defined `DOC_LAYOUT_HEADER` and `DOC_LAYOUT_NOTES` constants in `api/apps/erp/base/document.py` and used them in `accounting/views.py` and `stock/views.py`.
  - [Gemini] Renamed "Totals" tab to "Financials" in `accounting/views.py`.


---
## Framework Change: ERP user access control (org-scoped RBAC) + fix module registration + rename UserRole.company_id → org_id — revision (2026-05-18)
  - [Gemini] RBAC permission checking adjusted to remove company_id parameter, UserRole model simplified.


---
## Framework Change: Hierarchical org scope expansion & is_shared master data (2026-05-18)
  - [Gemini 2.5 Flash] Enhanced RouterFactory and Model.apply_filters for list-based scopes
