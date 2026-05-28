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
| `ggc` | Give git commit command text for all changes — do NOT execute, user runs it. always put ai name so later people know your quality | 
| `updd` | Update `docs/feature.md` (add only) and `docs/aras.md` if framework changed |
| `dde` | Don't do edit — no changes whatsoever |
| `rrc` | Re-read CLAUDE.md rules 1-3 before anything else |
dont run multi_agent directly, i will run it

# Aras Framework — Architecture Reference

> FastAPI + SQLAlchemy 2.0 backend · React 19 + TypeScript frontend
> **Detail tables** (classes, attributes, endpoints, components, file structure): `docs/framework_ref.md`
> **Reading rule**: Never full-read `framework_ref.md` — use only the exact line range shown in each pointer below.
> **Sync rule**: If line numbers in `aras.md` or `framework_ref.md` shift due to edits, update ALL affected `→ framework_ref.md L…` pointers in BOTH files immediately.

Aras is a general-purpose, metadata-driven application framework — not an ERP. It provides a code-first model registry, auto-generated CRUD APIs, metadata-driven UI, RBAC, workflow engine, multi-tenancy, and a modular app system where each app is an independently installable unit. Each app owns its own models and routes and appears directly in the sidebar. Any system can be built this way: a hospital patient registry, a school management system, a property rental platform — each as its own app. ERP domains (Accounting, Stock, CRM, etc.) are each their own top-level app, not sub-modules.

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
4. Apps are isolated by `app_name`; `parent_name` is available but not used for ERP — all ERP domains are top-level apps.

Full `manage.py` command list: → `framework_ref.md` L226–242

### App Registration Requirements (required for all apps)

Every app needs three things to have visible resources in the UI:

1. **views.py** — `Aras.View` subclass per model:
   ```python
   class WebPageView(Aras.View):
       model = WebPage
       title = "Pages"
       icon = "pi pi-file"
   ```

2. **app.py** — must import views (side-effect) and call `autodiscover_models`:
   ```python
   from core.logic.discovery import autodiscover_models
   from .models import *
   from . import views  # triggers View registration
   
   class WebApp(App):
       models = autodiscover_models(__name__, ["models"])
   ```
   Without `models = autodiscover_models(...)`, `cls.models` is empty and `get_menu_structure()` returns nothing.

3. **sync** — after adding a new app, run `python manage.py sync` to populate AppModel/ResourceModel/FieldModel in DB.

---

## Model Rules

- `__tablename__` — REQUIRED, `{table_prefix}_{table}` where `table_prefix` matches the app's `table_prefix` attr (e.g. `erp_accounting_accounts` for app `accounting` with `table_prefix="erp_accounting"`)
- `__features__` — `["audit"]`, `["audit", "workflow"]`, `["activatable"]`
- `__scoped_by__` — `[(col, fk_table)]` — auto-injects FK col + WHERE filter per JWT scope
- `__unique_together__` — `[("col_a", "col_b")]` — composite UniqueConstraint
- `info={"choices": [...]}` — emits select UI + narrows Pydantic field to `Literal[*choices]`
- `info={"form_hidden": True}` — hides from auto-form, still visible in API
- `__title__` is **removed** — use `View.title` instead
- `is_active` is NOT auto-provided — opt in via `__features__ = ["activatable"]`
- Auto-provided columns (never declare): `id`, `created_at`, `updated_at`, `created_by`, `updated_by`
- Full attribute list: → `framework_ref.md` L70–89

## Model Actions

### display_token response pattern
If a model action returns `ok({"display_token": token}, message="...")`, the frontend DynamicForm
automatically shows a copyable modal with the token. Use this for any action that generates a secret
the user must copy once (license tokens, API keys, one-time passwords).

## View Rules

- Title auto-derived from model class name (strips "Model"/"View" suffix, splits CamelCase).
- Only write a View to override title, add layout, or customize fields.
- `View._auto_register(model_cls)` ensures every model has a View on demand.
- Import views in `app.py`: `from . import views as _views  # noqa`

---

## Engineering Standard

Always use the **best** approach — not the simplest. Use simple only when it is genuinely the best. Build world-class, not "good enough".

## Development Mandates

1. Table naming: ALWAYS `{table_prefix}_{table}` — set `table_prefix` on the App class when it differs from `app_name` (e.g. app `stock` uses `table_prefix="erp_stock"`, tables are `erp_stock_products`)
2. After changing `models.py` or `app.py`: run `python manage.py sync` from `api/`
3. One file, one class — strict modularity
4. Never run long-running servers as foreground
5. Run from `api/` dir; `sys.path` must include `api/`
6. Models contain ONLY data/schema — never `__title__`, `__icon__`, or display attributes
7. Views contain ALL UI metadata — title, icon, fields overrides, layout
8. Every folder must have `__init__.py` — discovery uses `pkgutil.walk_packages`

App patterns, file structure, `autodiscover_models`, `menu_groups`: → `framework_ref.md` L245–337

---

## API Conventions

All routes prefixed `/api/v1/`. Underscores → hyphens. App/parent prefixes stripped from last path segment.

Example: App `accounting` (`table_prefix="erp_accounting"`), model `erp_accounting_accounts` → `/api/v1/accounting/accounts`

Full endpoint list: → `framework_ref.md` L130–153

## Endpoint Patterns

### Public endpoints (no auth)
Routers mounted via `App.routers = [router]` do NOT get auth by default. To add a public
endpoint (no JWT required), simply define the route without `Depends(get_current_user)`:

```python
router = APIRouter(prefix="/web", tags=["Web"])

@router.get("/pages/{slug}")
def get_page(slug: str, db: Session = Depends(get_db)):
    ...
```

This pattern is used by `apps/web/` for public CMS endpoints.

---

## Security & Config

Config from `.env` via `api/core/lib/settings.py`. Key vars: `SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS`, `ARAS_MODE`.

Auth chain: `require_admin → get_current_user → JWT decode → DB lookup` (`api/core/auth/service.py`).

RBAC: `RBAC.has_permission(db, user, resource, action)` · `RBAC.get_readable_resources(db, user)`

Logic modules + Manager classes: → `framework_ref.md` L104–127

---

## ERP Apps (`api/apps/erp/`)

ERP domains are top-level standalone apps — no parent app. Each inherits `Aras.App` directly and sets `table_prefix` to match its DB tables:

| app_name | table_prefix | app_label |
|---|---|---|
| `accounting` | `erp_accounting` | Accounting |
| `stock` | `erp_stock` | Stock |
| `hr` | `erp_hr` | Human Resources |
| `crm` | `erp_crm` | CRM |
| `asset` | `erp_asset` | Fixed Assets |
| `party` | `erp_party` | Parties |
| `pot` | `erp_pot` | Point of Transaction |
| `report` | `erp_report` | Reports |
| `config` | `erp_config` | Configuration |

Shared utilities live in `api/apps/erp/base/` (`saved_filter_router`, `series_router`, `SavedFilter`, ERP abstract bases). ERP abstract bases (`DocumentBase`, `LineItemBase`, `MasterDataBase`, `ConfigBase`) are ERP-specific — not framework primitives.

Full sub-app and base tables: → `framework_ref.md` L340–370

---

## Standard Apps (`api/apps/`)

| app_name | table_prefix | Key models |
|---|---|---|
| `saas` | `saas` | Plan, Subscription, LicenseToken, ActivationRequest |
| `web` | `web` | WebPage, WebMenuItem, ContactSubmission, SiteSetting |
| `notes` | `notes` | Note |
| `ticket` | `erp_ticket` | Team, Category, Ticket, TicketMessage |
| `dev` | `dev` | HandoffRun, TemplateAnnotation |

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

Full component/hook/route tables: → `framework_ref.md` L155–223

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

---
## Framework Change: Customize panel resource lookup fix + closePanel on navigation (2026-05-19)
  - [Claude Sonnet 4.6] `handleCustomize` in DynamicForm.tsx was querying `/aras_resources?name=<url-path>` — the `name=` param is ignored by the list endpoint (only `filters` JSON array is supported). Fixed to use `filters=[{field:'name', op:'=', value:tableName}]`. Also changed resource key source from `cleanResourcePath(resource)` (URL path) to `metadata.resource` (tablename). Added `key={resourceRecord.id}` to ListView to force remount on resource change. Added `closePanel()` on `location.pathname` change in MainLayout via `useUIStore`.

---
## Framework Change: ERP series seeds yaml + seed_series idempotent db param (2026-05-19)
  - [Claude Sonnet 4.6] `api/apps/erp/seeds/series.yaml` — declarative series definitions with correct `__tablename__` keys and `{prefix}{year}-{next_value:04d}` format. `seed_series.py` now loads from yaml; `run(db=None)` accepts optional session for reuse. Provisioner calls `seed_series(db=db)` during tenant setup. `api/apps/erp/seeds/demo.yaml` added as standard structure for installable demo data.


---
## Framework Change: LinkedDoc Auto-Discovery (2026-05-19)
- [Gemini 2.5 Flash] Refactored core `Model` to automatically discover linked documents via SQLAlchemy foreign key inspection, reducing the need for manual `__linked_docs__` declarations.

## Framework Change: POS Custom App Routers (2026-05-19)
- [Gemini 2.5 Flash] Added `App.get_routers()` support to allow apps to mount custom FastAPI routers alongside auto-generated ones.

---
## Framework Change: Document number fix + model column cleanup (2026-05-19)
  - [Claude Sonnet 4.6] `model.py`: `db.add(self)` moved before `before_save()` — `object_session(self)` was returning None for new objects, causing `DocumentBase.before_save` to skip number generation entirely. All new documents now get series numbers on creation.
  - [Claude Sonnet 4.6] `ItemAccount` switched from `LineItemBase` → `ErpBase` (removes unneeded qty/amount/sequence). `ItemLocation.min_qty`/`max_qty` removed. `Item.sku` removal and `ItemBundle.notes`/`amount` cleanup deferred to handoff run_id 15.
  - [Claude Sonnet 4.6] ERP series seeded via `python apps/erp/config/seed_series.py` (10 series entries).

---
## Framework Change: Migrate styling system to generic app- prefix & fix dark mode input bugs (2026-05-21)
  - [Antigravity] Completely renamed custom CSS variables and class selectors in `ui/src/index.css` to use a generic prefix (`--app-` / `.app-`), while mapping legacy `--aras-` tokens and `.aras-` selectors to guarantee 100% backward-compatibility for active React components.
  - [Antigravity] Corrected the dark-mode input styling bug by replacing hardcoded background (`#f8fafc`) and border (`#dfe5ee`) colors with theme-aware `var(--app-panel-soft)` and `var(--app-border)` variables, ensuring forms render beautifully in obsidian-indigo theme.
  - [Antigravity] Replaced hardcoded dark colors on line items, labels, and text with `var(--app-text)` so they are perfectly legible in dark mode.


---
## Framework Change: CSS prefix migration & dark mode input fixes (2026-05-21)
  - [Antigravity] Renamed CSS prefixes to app- with legacy alias compatibility mappings

## Open Source
Aras will be open sourced. AI attribution is required on every function.
Tag format: `# claude-sonnet-4-6`, `# gemini-flash`, `# gemini-pro`, `# chatgpt` etc.
Place the tag comment on the line above the function/class definition.
Be honest about quality: `# claude-sonnet-4-6 (bad)`, `# gemini-pro (needs review)` — let contributors know what to trust.


---
## Framework Change: i18n Architecture & Table Rename (2026-05-25)

### Table rename
- `aras_translations` → `translations` (translation_model.py, auto_migrate.py, installer.py, health_manager.py)

### i18n Architecture (Phase 1 — EN + ID)

**Web (React)**
- Static UI strings: `ui/src/locales/{en,id}.json` + `LanguageContext` (localStorage `aras_lang`)
- Dynamic content (field labels, resource titles): backend `TranslationService` via `?lang=` param on metadata endpoints
- Language switcher: Header component (Globe icon + EN/ID toggle)

**Mobile (React Native/Expo)**
- Same pattern: `mobile/src/locales/{en,id}.json` + `LanguageContext` (AsyncStorage `aras_lang`)
- Language switcher: SettingsScreen

**VocabularyContext** (existing): handles per-org profile label overrides (retail/school/coop) — independent of i18n lang.

### Roadmap kesiapan
| Phase | Scope | Arsitektur | Status |
|-------|-------|------------|--------|
| 1 | EN + ID | JSON locales + LanguageContext + TranslationService | In progress |
| 3 | Global Latin-based | Tambah locale file saja, tidak ada perubahan arsitektur | Ready |
| 2 | ASEAN CJK | Font CJK, RTL CSS (sudah dipersiapkan), charset | Requires font setup |

**RTL-readiness**: CSS harus pakai `margin-inline-start` bukan `margin-left`, `padding-inline` bukan `padding-left/right`, dan `dir="rtl"` di root. Persiapkan dari Phase 1 walaupun belum dipakai.

**Multi-currency**: Siapkan `currency_code` + `locale` di org settings. Format angka via `Intl.NumberFormat(locale, {style:'currency', currency})`. Pluggable tax engine per `country_code` di org settings.

---
## Framework Change: Audit hardening, explicit cascades, SaaS plan entitlements, and public i18n (2026-05-26)

### Request scope and generic writes
- `get_current_user()` now accepts only org scope headers: `X-Org-ID` or `X-Scope-Org-ID`.
- Unsupported `X-Scope-*` headers are rejected instead of being trusted as arbitrary scope values.
- `X-Org-ID` and `X-Scope-Org-ID` must match when both are sent.
- Generic `bulk-delete` and list-shaped `/batch` operations now fail on missing/out-of-scope records instead of silently skipping them.
- List-shaped `/batch` operations now commit successful operations atomically.

### Cascade delete rule
- Implicit FK auto-cascade in `Model._cascade_linked_docs()` is removed.
- Destructive linked deletes must be declared explicitly through `__linked_docs__ = [LinkedDoc(..., cascade=True)]`.
- SQLAlchemy relationship-level `cascade="all, delete-orphan"` remains valid for ORM-owned child collections.

### Startup writes
- Production API startup no longer runs registry sync/bootstrap writes.
- `Sync.sync_all()` and bootstrap still run in `DEBUG`/`TESTING`; production deploys must run migrations and sync explicitly.

### SaaS plan entitlement payload
- SaaS plan payloads normalize `features.apps` for both public plan cards and portal app gating.
- Public pages show only the current public tiers: `free`, `lite`, `growth`, `business`.

### Public web i18n
- Public landing and signup pages now use `LanguageContext` and `ui/src/locales/{en,id}.json`.
- `LanguageContext.t()` resolves both flat keys (`"nav.dashboard"`) and nested object paths.
- Public pages include EN/ID toggles and persist language in `localStorage` key `aras_lang`.


---
## Framework Change: Framework remaining items — all NOT DONE and HALF from plan.md verified against actual codebase — revision (2026-05-26)
  - [GPT (codex)] Added reusable FormSettings component and WebSocket client bootstrap
