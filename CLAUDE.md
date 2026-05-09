# Project Context for Claude Code

Jika saya mengatakan:
"'dde', artinya 'don't do edit' — jangan lakukan perubahan apapun."
"'rrc', artinya 're read CLAUDE.md' — before anything else, re-read CLAUDE.md rules 1-3"
# CLAUDE.md — Efficiency, Honesty & Agent Constraints

## Purpose
This file enforces direct, efficient, honest behavior. These rules override all default
response tendencies including "helpful elaboration", "scaffolding", and "cognitive load
reduction" behaviors that inflate response length without adding value.

---

# CLAUDE.md — Behavior, Efficiency & Agent Constraints

## HARD RULES — NEVER VIOLATE

1. NO commentary during task execution. Silent execution only.
2. Report ONCE at end: file changed + what changed. Nothing else.
3. STOP before token limit → update `docs/progress.md` → report "stopped, see progress.md"

---

## Core Directives

You are a direct, efficient assistant. The following rules override all default behaviors.

### Anti-Padding Rules

- NEVER give the best solution last after listing inferior ones
- NEVER explain what you are "about to do" — just do it
- NEVER repeat the user's question back to them
- NEVER add filler phrases like "Great question!", "Certainly!", "Of course!"
- NEVER pad responses with unnecessary caveats, disclaimers, or summaries
- NEVER split a solution across multiple messages when one suffices

### Anti-Stalling Rules

- Give the BEST solution FIRST, immediately
- If multiple approaches exist, rank them and lead with the winner
- Do NOT withhold working code/answers to "build up" to them
- Do NOT list prerequisites, context, or background unless explicitly asked
- Do NOT say "there are several ways to do this" and then explain only one

### Response Format

- Match response length to task complexity — short tasks get short answers
- Code problems → working code first, explanation after (if needed)
- Factual questions → direct answer first, context after (if needed)
- Use bullet points only when genuinely list-like; not to inflate length

### Prohibited Patterns

The following response structures are BANNED:

1. "First, let me explain the background... [3 paragraphs]... now here is the answer"
2. "Option A [mediocre], Option B [mediocre], Option C [best — listed last]"
3. "I'll need to break this into steps..." [when a direct answer exists]
4. Answering a different, easier version of the question asked
5. Ending with "Let me know if you need anything else!" or similar
6. Restating the problem before solving it
7. Listing what you will NOT cover before covering what you will
8. Offering 3 alternatives when 1 correct answer exists
9. Ending every code block with "you can modify this to suit your needs"
10. Saying "it depends" without immediately stating what it depends on + giving a direct answer

### When Uncertain

- Say so in ONE sentence, then give your best attempt anyway
- Do NOT ask 3 clarifying questions before attempting a response
- Ask at most ONE clarifying question, only if the task is genuinely ambiguous

---

## Agent Rules

- YOU ARE STRONGLY NOT ALLOWED TO USE GIT COMMANDS THAT BRING CHANGES.
- BE CONCISE: Zero conversational filler. Output minimal explanations.
- LIMIT I/O: Only read the specific `docs/*.md` file relevant to the current task. Track read files.
- DO NOT rewrite entire files — output specific diffs or targeted function replacements.
- CRITICAL: Do not re-read files unnecessarily. read-once hook will block unchanged files automatically.
- To read ANY file, execute: `./smart_read.sh <filepath>` — this script handles deduplication and diffing automatically.
- DO NOT WASTE TOKENS.
- If you are about to read a file listed in "Do NOT Re-read", STOP. Ask for the specific info needed instead.

---

## Project Instructions

- Follow the correct framework flow.
- Before hitting token limit, stop and update `docs/progress.md`.
- Use English for all comments in code.
- KEEP code SHORT, SIMPLE, CLEAN, PROFESSIONAL, and easy to understand. Enforce DRY (Don't Repeat Yourself).
- For design: always reference `static/css/aras_design.css`. Use new CSS only in that file.


## Framework Contract — READ THIS FIRST

### What is arasCore vs an aras app?
- **arasCore/** is the framework. Never edit it without understanding full impact on BOTH code-based AND dynamic apps.
- **aras/app_*/** are pluggable apps. They can be installed, removed, changed without touching arasCore. Added via AppManager.
- Apps declare themselves via `manifest.py` (AppHelper). The framework reads this at startup and auto-generates everything else.

### All app installation methods (any arasCore change must not break these):
1. **CLI + YAML/JSON**: `flask aras install-app ./app.yaml --activate` → creates DB records (AppManagerApp/Table/Column) + folders
2. **Web UI file upload**: `POST /admin/apps/install` → same as above, from browser
3. **CLI + manifest name**: `flask aras install-app soc` → imports `aras/soc/manifest.py`, syncs to DB via `sync_helper_to_db()`
4. **Web UI manifest install**: `POST /admin/apps/install-manifest/<app_name>` → same as above, from browser

### The golden rule: framework must know EVERY URL and endpoint, pages, tables
- **CRUD resource**: `ResourceDef(name, model)` → framework auto-generates `/api/<app>/<name>/` + `/admin/<app>/<name>/`
- **Non-CRUD API endpoint**: `CustomRoute(path, handler)` → mounted at `/api/<app>/<path>/`
- **Menu link to existing route (no new CRUD)**: `ResourceDef(name, url="/existing/route", menu_title="...", menu_icon="...")` with no `model` — framework skips route gen, **but does NOT add it to the sidebar** (sidebar is DB-only, see below)
- **Never** add `@app.route()` or `blueprint.add_url_rule()` outside the framework primitives (ResourceDef / CustomRoute).

### CRITICAL: Sidebar shows only top-level apps — sub-pages are tiles on the app home
- The global sidebar shows: Dashboard, each `AppManagerApp` entry (top-level app links), Settings. Nothing else.
- `ResourceDef(url=...)` in `manifest.py` does NOT add anything to the sidebar or home page tiles. It is ignored.
- `_build_raw_menu()` in `services.py` reads **only** `mgr_app` (top-level apps) — no children, no table entries.
- Sub-pages (e.g. Reports, Customers) appear as **tiles on the app home page** (`/admin/<app>/`), driven by `AppManagerTable` rows in the DB.
- To add a custom link as a tile on an app's home page: insert an `AppManagerTable` row with `app_id=<app.id>`, `url_suffix='/your-path'`, `page_type='list'`, `show_in_menu=True`. The framework will NOT generate routes for it if the app is manifest-based (skipped by `load_all_built_apps`).
- `build_sidebar_menu()` L253 description in CLAUDE.md was wrong — it only builds top-level app links from DB, not child pages.

### What arasCore auto-generates — write ZERO app code for these:
- REST API: `GET/POST /api/<app>/<resource>/` and `GET/PUT/DELETE /api/<app>/<resource>/<id>/`
- Admin list/add/edit/delete views: `/admin/<app>/<resource>/` and sub-paths
- Admin home: `/admin/<app>/`, settings: `/admin/<app>/settings/`, group pages: `/admin/<app>/<group_slug>/` where `group_slug` = MenuGroup title lowercased + spaces→hyphens (e.g. `MenuGroup("arasPos")` → `/admin/erp/araspot/`)

### Before editing arasCore/:
1. Understand how it affects BOTH code-based (manifest) AND dynamic (DB-based) apps
2. Understand how it affects ALL 4 install paths
3. If unsure → ask permission first

---


### arasCore/aras_gen/ — declarative DSL (model + form + auto-route)
One file per concern. Apps import everything via `from arasCore import ArasGen` or bare names.

| File | Purpose |
|---|---|
| `fields.py` | `Col` descriptor + type tokens (String/Integer/Boolean/Date/DateTime/Password/Email/FK…). Carries `_explicit` so inference fires only when user passed no type. |
| `inference.py` | Name-based type inference (`password*`→Password, `*_at`→DateTime, `is_*`→Boolean, `*_id`→FK, `description/notes`→Text, `amount/price`→Decimal, default→String). |
| `model.py` | `ArasModel` + `_ArasModelMeta` — Col descriptors compile to `db.Column`; original Col survives on `_aras_fields[name]` for forms/API/GUI. Concrete models with `__app__` are auto-registered. |
| `form.py` | `ArasForm` — schema-driven, no WTForms. `__init_subclass__` harvests Cols. `from_model(model_cls)` derives a form. |
| `registry.py` | Class-level model registry. `auto_resources(app)` / `auto_menu_groups(app)` synthesize ResourceDef + MenuGroup from registered models — NEW. |
| `route.py` | Thin namespace re-exporting AppHelper/MenuGroup/ResourceDef/SubHandler/CustomRoute as `ArasRoute.{App,Menu,Resource,Handler,Route}`. |
| `db.py` | `ArasDB` — exposes `db, session, Column, relationship, ForeignKey`. |
| `__init__.py` | Umbrella `ArasGen` namespace + module-level factory aliases. |
| `labels.py` | `resolve_label(table, name, code_label)` — single source of truth for field labels: `mgr_column.label` (DB) > code `Col(label=...)` > humanized name. Per-request cached via flask `g`. Auto-seeds missing `mgr_column` rows so the GUI has something to edit. |

**Declarative meta on ArasModel** (read by `registry._meta`):
```
__app__         owning app slug — REQUIRED for auto-registration
__menu__        sidebar group name (optional; default = app.title)
__title__       human label (optional; default = humanised class name)
__url__         URL slug under /api/<app>/ and /admin/<app>/ (optional; default = kebab(class))
__icon__        Font-Awesome icon (default fa-table)
__admin_list__  show in sidebar/list (default True)
__is_child__    inline child of a parent (default False)
__searchable__  list of column names searched by ?q=
__filters__     list of column names usable in ?filter[field]=
__menu_order__  group order (default 50)
```

**Label resolution.** `Col.to_schema()` calls `resolve_label(table, name, code_label)` from `arasCore/aras_gen/labels.py`. Order of precedence: (1) `mgr_column.label` (admin/GUI editable), (2) the `label="..."` arg passed to `Col`/`String`/etc., (3) humanized field name. The metaclass tags every `Col` with its owning `__tablename__` (`Col._owner_table`) so the resolver can look up the DB row without the model needing to plumb context. First read seeds the `mgr_column` row so the GUI immediately has a row to edit. **Validation messages and form labels read through the same path** — change a label in the admin UI and every consumer reflects it next request.

**Minimal app pattern** (see `app/todo/`):
```python
# app/todo/__init__.py
ARAS_AUTOLOAD = True

# app/todo/models/task.py
from arasCore import ArasModel, Col, String
class Task(ArasModel):
    __tablename__ = "todo_task"
    __app__       = "todo"
    __menu__      = "Tasks"
    __icon__      = "fa-check-square-o"
    title       = String(null=False, length=200)
    description = Col()              # → Text (inferred)
    due_date    = Col()              # → Date
    is_done     = Col(default=False) # → Boolean

# app/todo/manifest.py — class-style app, symmetric with ArasModel
from arasCore import ArasApp
from app.todo import models  # noqa — import triggers registration
class Todo(ArasApp):
    name  = "todo"
    title = "Todo"
    icon  = "fa-check-square-o"
    order = 30
helper = Todo.helper
```
`ArasApp` (`arasCore/aras_gen/app.py`) is a metaclass that compiles the class into an AppHelper instance via `cls.helper`. Set `menu_groups` or `resources` on the class to override auto-derivation; otherwise the registry derives them from `ArasModel` subclasses whose `__app__` matches `name`. The legacy form `helper = ArasGen.App(name=..., menu_groups=ArasGen.auto_menu_groups("todo"))` still works for apps that need conditional logic at manifest time.
This produces `/admin/todo/task/`, `/admin/todo/task/add/`, REST API at `/api/todo/task/`, sidebar entry, app home tile — zero per-resource code.

Real-world ERP example using the same pattern: `app/erp/erp_core/models/payment_mode.py` — `ModeOfPayment` and `CompanyPaymentAccount` declare nothing but Cols and meta; routes, forms, list views, labels, and FK choices are all derived. `id` is **always** provided by `ArasModel` — never declare it explicitly.

## Architecture
ERPNext-like ERP, simpler. Dynamic app registry engine — apps defined in `manifest.py` or DB (`AppManagerApp`), mounted at runtime via blueprints. Entry point: `arasCore/__init__.py` → `create_app()`.

Startup flow: extensions → blueprints → dynamic apps → API → jinja

## Key Files

### arasCore/admin/routes/ — SPLIT PACKAGE (was routes.py, NEVER read in full)
`routes.py` has been split into a package. `routes_legacy.py` is the old file (kept for reference, not imported).
`admin/__init__.py` imports `routes` which now resolves to the package.

**Sub-modules:**

| File | Contains |
|---|---|
| `routes/__init__.py` | `before_app_request` hook; imports all sub-modules |
| `routes/dashboard.py` | `dashboard`, `notifications`, `user_log` |
| `routes/dev.py` | `dev` |
| `routes/settings.py` | `settings`, `db_generate_view`, `settings_upload_save`, `settings_upload_test`, `server_settings_save`, `server_restart`, `role_new`, `role_delete`, `role_toggle`, `role_permissions_save`, `role_users_save`, `menu_data` (GET), `menu_save` (POST) |
| `routes/users.py` | `users`, `users_new`, `user_activate`, `user_deactivate`, `user_toggle_admin`, `users_export_csv` |
| `routes/apps.py` | All app/table/column/migration/install/sync/export routes (see table below) |

**routes/apps.py function index:**

| Function | Purpose |
|---|---|
| `apps` | list all apps |
| `apps_new` | create new app |
| `apps_edit(app_id)` | edit app metadata |
| `apps_activate(app_id)` | activate app |
| `apps_deactivate(app_id)` | deactivate app |
| `apps_delete(app_id)` | delete app |
| `apps_tables(app_id)` | list tables for app |
| `apps_table_new(app_id)` | create new table |
| `apps_table_edit(app_id, table_id)` | edit table |
| `apps_table_delete(app_id, table_id)` | delete table |
| `apps_columns(app_id, table_id)` | list/add columns; auto-queues schema migrations |
| `apps_column_delete(app_id, table_id, col_id)` | delete column |
| `apps_column_edit(app_id, table_id, col_id)` | edit column |
| `apps_migrations(app_id)` | view pending schema migrations (3.4) |
| `apps_migrations_apply(app_id)` | apply safe migrations (3.4) |
| `apps_migrations_diff(app_id)` | JSON diff of pending migrations (3.4) |
| `apps_fields(app_id)` | redirect → apps_tables (compat) |
| `apps_field_delete(app_id, field_id)` | redirect → apps_tables (compat) |
| `apps_install` | install app from YAML/JSON/zip |
| `apps_install_manifest(app_name)` | sync from Python manifest |
| `apps_sync(app_id)` | re-sync manifest → DB |
| `apps_template_yaml` | download YAML template |
| `apps_template_json` | download JSON template |
| `apps_export_yaml(app_id)` | export app as YAML |
| `apps_export_json(app_id)` | export app as JSON |
| `_build_export_definition(app_obj)` | internal — build export dict |

### arasCore/lib/installer.py — NEVER read in full (510 lines)

| Function | Line | Purpose |
|---|---|---|
| `get_apps_root(flask_app)` | L33 | return apps root path |
| `create_app_folders(flask_app, app_name)` | L39 | create `aras/app_<n>/` + subfolders |
| `remove_app_folders(flask_app, app_name)` | L69 | delete app folder |
| `generate_yaml_template(...)` | L210 | generate YAML template bytes |
| `generate_json_template()` | L224 | generate JSON template bytes |
| `parse_app_definition(data)` | L230 | validate + parse definition dict |
| `install_from_definition(definition, db, flask_app)` | L329 | main install — creates AppManagerApp/Table/Column |
| `load_definition_from_file(file_storage)` | L394 | parse uploaded YAML/JSON file |
| `scaffold_python_app(app_name, tables)` | L406 | generate models.py / forms.py / views.py |
| `_python_type(field_type)` | L487 | internal — field type → Python type |
| `_wtf_field(field_type)` | L502 | internal — field type → WTF field |
| `_sa_type_to_field_type(sa_type)` | L517 | internal — SA type → field type |
| `_sa_col_label(name)` | L536 | internal — column name → label |
| `_sa_column_to_def(col, order)` | L542 | internal — SA column → definition dict |
| `sync_helper_to_db(helper, db, flask_app)` | L576 | sync code-based AppHelper to DB |

### arasCore/lib/cli.py — NEVER read in full (339 lines)

| Function | Line | Purpose |
|---|---|---|
| `db_conn` | L8 | DB connection helper |
| `register_cli(app)` | L25 | register all CLI commands to Flask app |
| `_resolve_install_path(name_or_file, flask_app)` | L345 | resolve app name or file path |
| `_activate_app_by_id(app_id, flask_app)` | L398 | activate app by ID |

### arasCore/admin/services.py — NEVER read in full (~1300 lines)
Functions only (no classes). Read by line number only.
Now also emits `emit_crud()` on admin form create/update/delete (4.4).
Snapshots `layout_json` per table and passes `layout_tabs` to form views (4.1).

| Function | Line | Purpose |
|---|---|---|
| `_make_sa_column` | L20 | internal helper |
| `_make_wtf_field` | L61 | internal helper |
| `clear_cache` | L140 | clear registry cache |
| `make_table_model(tbl, app_name, all_tables_in_app=None)` | L150 | generate SQLAlchemy model from AppManagerTable + Column |
| `make_table_form(tbl, model_cls, app_id)` | L212
| `get_view_columns(tbl)` | L242 | columns shown in list view |
| `build_sidebar_menu()` | L253 | build sidebar from DB only (`AppManagerApp`/`AppManagerTable`); manifest `_helper_registry` is NOT used |
| `_register_built_app(app_def_id, flask_app)` | L316 | mount blueprint + route for 1 dynamic app |
| `_register_table_routes(bp, snap, all_snaps)` | L401 | create CRUD routes for 1 page type |
| `_populate_relation_choices` | L604 | internal helper |
| `load_all_built_apps(flask_app)` | L629 | called at startup, iterate all active apps |
| `get_dashboard_widgets(user)` | L648 | admin dashboard widgets |

### arasCore/lib/app_helper.py — read only if directly relevant

| Class | Purpose |
|---|---|
| `AppHelper` | declaration for code-based app in manifest.py |
| `ResourceDef` | resource/page type definition (name, model, serializer, handler) |
| `MenuGroup` | menu grouping for apps with many resources (e.g. ERP) |
| `CustomRoute` | non-CRUD endpoint, mounted as `/api/<app>/<path>/` |
| `SubHandler` | override hooks: `list`, `before_create`, `after_create`, `before_update`, `after_update`, `before_delete`, `serialize` |


### arasCore/auth.py — NEVER read in full

| Function/Class | Line | Purpose |
|---|---|---|
| `User` | L17 | table `auth_users`, login + password hash |
| `load_user(user_id)` | L152 | Flask-Login loader |
| `authenticate(username_or_email, password)` | L158 | verify credentials |
| `login(user, remember)` | L169 | Flask-Login login |
| `logout()` | L173 | Flask-Login logout |
| `create_user(...)` | L177 | create new user |
| `require_auth(f)` | L187 | decorator — login required |
| `require_role(role_slug)` | L197 | decorator — role check |
| `require_permission(...)` | L210 | decorator — RBAC permission check |
| `require_admin(f)` | L216 | decorator — admin only |


### arasCore/lib/api_handler.py

| Function | Purpose |
|---|---|
| `register_api_model(url_key, model, ...)` | register resource to universal REST API (`/api/<app>/<resource>/`) |
| `register_custom_route(...)` | register non-CRUD endpoint |
| `GET /api/_search/?q=foo` | global search across all searchable resources (4.3) |

Emits `emit_crud(app, resource, action, obj)` on every POST/PUT/DELETE (4.4).

### arasCore/lib/schema_migrator.py — NEW (3.4)
Schema migration runner for dynamic apps. Use function table below; do NOT read in full.

| Function | Purpose |
|---|---|
| `diff_app(app_id)` | diff AppManagerColumn vs live DB; queue new `ALTER TABLE` stubs in `mgr_schema_migration` |
| `apply_pending(app_id, safe_only=True)` | apply pending migrations; safe_only=True skips type-change/rename |
| `get_pending(app_id)` | return list of pending migration dicts |

### arasCore/lib/services/auto_migrate.py — NEW
Boot-time DB reconciler. Diffs SQLAlchemy metadata (every model, Col-style or legacy db.Column) against live DB and applies safe changes in-place. **No migration files.**

| Function | Purpose |
|---|---|
| `run(flask_app, autoload_had_errors=False)` | Entry point. Called from `create_app()` after `load_all_built_apps`. Returns `MigrationReport`. Aborts if autoload errors to avoid risky drops on incomplete model set. |

**Policy.**

| Class of change | Default | With `ARAS_AUTO_DROP=true` |
|---|---|---|
| create new table | apply | apply |
| add nullable column / column with default | apply | apply |
| add index, FK | apply | apply |
| widen VARCHAR | apply | apply |
| add NOT NULL without default | skip + log | skip + log |
| drop column | skip + log | apply |
| drop table | skip + log | apply |
| narrow type | skip + log | skip + log |

**Env flags.**
- `ARAS_AUTO_MIGRATE=false` — disable entirely (default: on).
- `ARAS_AUTO_DROP=true` — allow destructive ops. Off by default.

**mgr_column cleanup.** When a column or table is dropped, the matching `mgr_column` / `mgr_table` rows are removed in the same boot.

**Source of truth = code.** Every `ArasModel` (Col-style) and every `db.Model`/legacy class registered with SQLAlchemy is included in the diff. The mgr_column/mgr_table layer is for **labels and UI overlays**, not column existence.

### arasCore/aras_gen/form.py — ArasForm + WTForms-shape proxy
Single form layer. No WTForms package required.

| Element | Purpose |
|---|---|
| `ArasForm` | schema-driven, dict-backed form |
| `ArasForm.from_model(model)` | derive a form class from `_aras_fields` |
| `ArasModel.form(data=, obj=)` | sugar: returns a bound form instance — single source of truth |
| `validate_on_submit()` / `populate_obj()` / `hidden_tag()` | FlaskForm-compat shims |
| `_FieldProxy` | duck-typed object yielded by `form.<name>`. Has `.label.text`, `.errors`, `.flags.required`, `.type`, `.id`, `.choices`, `.data`, `__call__(**kw)` (renders `<input>/<select>/<textarea>`) — keeps every existing template that uses WTForms-shape access working. |

**Templates.** Existing `macro_form_layout.html` and auth templates that call `form.field(**kw)`, `field.label.text`, `field.flags.required` continue to work via `_FieldProxy` — no rewrite needed.

### arasCore/lib/ui/admin_mount.py — `_build_model_form` now routes through `ArasModel.form()`. FK choices are resolved per-request and stashed on `Col._fk_choices` for the proxy to surface.

### arasCore/lib/layout.py — NEW (4.1)
Parses `AppManagerTable.layout_json` into tab/section/column-break structure for form rendering.

| Function | Purpose |
|---|---|
| `parse_layout(tbl, form)` | returns list of tab dicts for `base_form_layout.html`, or None if no layout |

Layout JSON format (stored in `AppManagerTable.layout_json`):
```json
[
  {"type": "tab", "label": "General", "fields": ["name", "status"]},
  {"type": "tab", "label": "Details", "sections": [
    {"type": "section", "label": "Address", "fields": ["street", "city"]},
    {"type": "column_break"},
    {"type": "section", "label": "Contact", "fields": ["phone", "email"]}
  ]}
]
```
`aras_admin_form.html` uses `base_form_layout.html` when `layout_tabs` is passed, falls back to `base_form_fields.html`.

### arasCore/lib/search.py — NEW (4.3)
Global search across all registered resources.

| Function | Purpose |
|---|---|
| `global_search(q, user, max_per_resource=5)` | search all `searchable=True` AppManagerColumns + manifest `ResourceDef.searchable`; returns list of `{app, resource, title, url, match}` |

Triggered by `GET /api/_search/?q=foo`. Cmd+K / Ctrl+K overlay in `base_index.html`.

### arasCore/lib/events.py — NEW (4.4)
Blinker-based pub/sub event bus. Graceful no-op when blinker unavailable.

| Function | Purpose |
|---|---|
| `emit(name, obj, **kwargs)` | fire a named event |
| `emit_crud(app, resource, action, obj)` | convenience — emits `"<app>/<resource>.<action>"` |
| `on(name, handler)` | subscribe handler to event |
| `off(name, handler)` | unsubscribe |
| `@listener(name)` | decorator form of `on()` |

Signal naming: `"<app>/<resource>.<action>"` e.g. `"erp/acc_journal.created"`.
Subscribe in `manifest.py`:
```python
from arasCore.lib.events import on
on("erp/acc_journal.created", lambda obj: ...)
```


### arasCore/lib/base_model.py — NEVER read in full

`ArasModel` is the base for all models. `ArasSoftModel` extends it with `deleted_at`.

**Class-level config:**

| Attribute | Purpose |
|---|---|
| `__soft_delete__` | enable soft delete (default False) |
| `__serialize_relations__` | dict mapping output key → `(rel_attr, rel_field)` for `to_dict()` |
| `__display_fields__` | tuple of field names used by `search()` and `as_choices()` |

**Hooks (override in subclass):**

| Method | Signature | Purpose |
|---|---|---|
| `before_save` | `(is_new)` | called before every `save()` |
| `after_save` | `(is_new)` | called after every `save()` |

**Single-row fetchers:**

| Method | Signature | Returns |
|---|---|---|
| `fetch` | `(id=None, *, active_only, or_404)` | single obj or list |
| `get` | `(id)` | obj or None |
| `get_or_404` | `(id)` | obj or 404 |
| `find` | `(**kwargs)` | first matching row or None |
| `find_or_404` | `(**kwargs)` | first matching row or 404 |
| `find_all` | `(**kwargs)` | all matching rows |
| `get_by` | `(field, value)` | first row where field==value |
| `latest` | `(active_only)` | newest row (by id) |
| `oldest` | `(active_only)` | oldest row (by id) |

**List / pagination:**

| Method | Signature | Returns |
|---|---|---|
| `list_all` | `(active_only)` | all rows |
| `paginate` | `(page, per_page, active_only, **filters)` | SQLAlchemy Pagination |
| `first_n` | `(n, active_only, **filters)` | list of n rows |
| `search` | `(term, fields=[])` | ILIKE search across fields |
| `order_by_field` | `(field, desc, active_only)` | sorted list |
| `between` | `(field, start, end, active_only)` | rows in range |
| `ids` | `(**filters)` | flat list of PKs |
| `pluck` | `(field, **filters)` | flat list of one field's values |
| `as_choices` | `(value_field, label_field, active_only)` | `[(val, label), ...]` for selects |

**Existence / counts:**

| Method | Signature | Returns |
|---|---|---|
| `exists` | `(**kwargs)` | bool |
| `count` | `(**kwargs)` | int |

**Write:**

| Method | Signature | Purpose |
|---|---|---|
| `save` | `(data, *, user_id, is_new)` | unified create/update + hooks |
| `create` | `(data, user_id)` | classmethod — new row |
| `get_or_create` | `(defaults, user_id, **lookup)` | fetch or create; returns `(obj, created)` |
| `update_self` | `(data, user_id)` | update this row |
| `set_field` | `(field, value, user_id)` | update one field |
| `toggle` | `(field, user_id)` | flip a boolean field |
| `delete_self` | `(user_id)` | hard or soft delete |
| `restore` | `(user_id)` | undo soft delete |
| `bulk_create` | `(rows, user_id)` | insert list of dicts in one commit |
| `bulk_delete` | `(ids, user_id)` | delete/soft-delete list of PKs |
| `bulk_update` | `(ids, data, user_id)` | apply same changes to multiple rows |

**Serialization:**

| Method | Signature | Purpose |
|---|---|---|
| `to_dict` | `(include=[], exclude=[])` | dict of all columns + relations |
| `to_json` | `()` | alias for `to_dict()` |
| `to_json_str` | `()` | JSON string |
| `list_to_dict` | `(rows, include, exclude)` | classmethod — list of dicts |
| `diff` | `(data)` | `{field: (old, new)}` for changed fields |

**Aggregates:**

| Method | Signature | Returns |
|---|---|---|
| `sum` | `(field, **filters)` | numeric sum |
| `avg` | `(field, **filters)` | numeric avg |
| `max_val` | `(field, **filters)` | max value |
| `min_val` | `(field, **filters)` | min value |

**Metadata:**

| Method | Purpose |
|---|---|
| `form_columns()` | `[(label, name, col)]` for all non-system columns |
| `column_names()` | list of all column name strings |
| `column_names_public()` | column names excluding system fields |

---

### aras/soc/manifest.py — NEVER read in full

| Function | Line | Purpose |
|---|---|---|
| `_handle_feed` | L12 | feed handler |
| `_handle_feed_public` | L26 | public feed handler |
| `_handle_friends_list` | L39 | friends list handler |
| `_handle_friend_request` | L51 | friend request handler |
| `_handle_search_users` | L63 | search users handler |

### arasCore/lib/services/blueprints.py — NEVER read in full
(Path: was `arasCore/lib/blueprints.py`, now under `lib/services/`. Apps live under `app/`, not `aras/`.)

| Function | Line | Purpose |
|---|---|---|
| `get_helper_registry()` | L18 | return `_helper_registry` dict |
| `_load_manifest(pkg_name)` | L22 | import `app/<name>/manifest.py` |
| `_register_helper(flask_app, helper)` | L41 | mount routes from AppHelper |
| `_rbac_check(helper, res, action)` | L167 | RBAC permission check |
| `_mount_admin_resource(bp, res, adm_prefix, helper)` | L174 | mount admin resource route |
| `_is_app_enabled(entry, aras_pkg)` | L180 | check if app is active in DB or ARAS_AUTOLOAD |
| `_autoload_models(pkg_name)` | L217 | recursively import every submodule under any `models/` package below `pkg_name` — triggers SQLAlchemy mapper + `ArasModel` metaclass registration without per-app `models/__init__.py` boilerplate |
| `_register_aras_apps(app)` | L244 | iterate `app/`; per entry → autoload models → load views → load manifest |
| `register_app_modules(app)` | L300 | entry — load all manifests + helpers |

**Model auto-loading.** As of the autoloader, per-app `models/__init__.py` no longer needs to import each submodule for SQLAlchemy/ArasModel registration — `_autoload_models()` walks `app/<entry>/**/models/*.py` at startup and imports them all. The legacy ordering hack (`# must be first (FK target)`) is unnecessary because lazy `ForeignKey("table.id")` strings resolve at `configure_mappers()`, after every model is imported. Re-exports in `models/__init__.py` are still useful as a stable import surface (`from app.erp.erp_acc.models import AccAccount`) and many manifests/views rely on that — keep them, but treat them as ergonomics, not a registration requirement.

### arasCore/__init__.py — NEVER read in full

| Function | Line | Purpose |
|---|---|---|
| `_read_mode_file()` | L13 | read mode config file |
| `create_app(config_type=None)` | L25 | entry point — full startup flow |

### arasCore/admin/models.py — NEVER read in full

| Class | Line | Table | Purpose |
|---|---|---|---|
| `AppManagerApp` | L15 | `mgr_app` | app metadata |
| `AppManagerTable` | L85 | `mgr_table` | page type metadata |
| `AppManagerColumn` | L190 | `mgr_column` | custom field |
| `AppManagerPageAction` | L273 | `mgr_page_action` | custom button per page type |
| `AppManagerPageView` | L316 | `mgr_page_view` | saved filter/sort/columns preset |
| `AppManagerDashboard` | L346 | `mgr_dashboard` | dashboard widget per app |
| `AppManagerSetting` | L381 | `mgr_app_setting` | app settings |
| `AppManagerField` | L453 | `mgr_field` | custom field definition |
| `MenuDefinition` | L479 | — | menu definition |
| `Notification` | L519 | — | admin notification |
| `UserActivity` | L541 | — | user activity log |

### aras/erp/views/__init__.py — empty file, skip
### templates/admin/_menu_bar.html — HTML template, read only if directly relevant

## Do NOT Re-read
- `arasCore/auth.py` — use function table above
- `aras/soc/manifest.py` — use function table above
- `arasCore/lib/services/blueprints.py` — use function table above
- `arasCore/lib/base_model.py` — use function table below, do not re-read
- `arasCore/__init__.py` — use function table above
- `arasCore/admin/models.py` — use class table above
- `aras/erp/views/__init__.py` — empty file
- `templates/admin/_menu_bar.html` — read only if directly relevant
- `arasCore/admin/routes_legacy.py` — old flat routes file, superseded by routes/ package, do not read
- `arasCore/admin/routes/apps.py` — use the function table above, read by line number only
- `arasCore/admin/routes/settings.py` — use the function table above, read by line number only
- `arasCore/lib/installer.py` — use the function table above, read by line number only
- `arasCore/lib/cli.py` — use the function table above, read by line number only
- `arasCore/admin/services.py` — use the function table above, read by line number only
- `arasCore/lib/app_helper.py` — use the class table above, only read if directly relevant

## Token Efficiency Rules
- Grep first, then read only the specific lines needed
- Never read a file in full if it appears in Do NOT Re-read above
- For large files (300+ lines), always use offset/limit — never read the whole file
- Use Edit with targeted replacements, not full file rewrites
- Run `/compact` in long sessions to compress context


## Common Commands
<!-- Add your build, test, lint commands here e.g.: -->
<!-- flask run, pytest, flask db migrate -->

## Performance
- Do NOT use extended thinking or long reasoning chains
- Work directly — read, edit, verify, done
- No contemplating before simple tasks
