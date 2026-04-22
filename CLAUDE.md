# Project Context for Claude Code

## Project Instructions
- Report only at the end, briefly. No explanations during task execution.
- Follow the correct framework flow (SEE docs/MAIN.md).
- This app is similar to ERPNext in function and system but simpler. See ERPNext code in `erpnext-develop/`.
- Before hitting limit, stop and update `docs/progress.md`.
- Use English for all comments in code.
- DONT answering in every task. Just do task and report in the end.
- KEEP code SHORT, SIMPLE, CLEAN, PROFESSIONAL, BEAUTY, and easy to understand

## Agent Rules
- READ DIFF ONLY
- BE CONCISE: Zero conversational filler. Output minimal explanations.
- LIMIT I/O: Only read the specific `docs/*.md` file relevant to the current task. Track read files.
- DO NOT rewrite entire files — output specific diffs or targeted function replacements.
- Use absolute imports from `aras` or `arasCore`.
- CRITICAL: Do not re-read files unnecessarily. read-once hook will block unchanged files automatically.
- CRITICAL: You are strictly FORBIDDEN from using native Read, View, or cat tools to read code files. To read ANY file, execute: `./smart_read.sh <filepath>` — this script handles deduplication and diffing automatically.
- DO NOT WASTE TOKENS. Prefer Grep over Read to locate code before reading. Use offset/limit for large files.
- If you are about to read a file listed in Do NOT Re-read, STOP. Ask me for the specific info you need instead.

## Framework Contract — READ THIS FIRST

### What is arasCore vs an aras app?
- **arasCore/** is the framework. Never edit it without understanding full impact on BOTH code-based AND dynamic apps.
- **aras/app_*/** are pluggable apps. They can be installed, removed, changed without touching arasCore. Added via AppManager.
- Apps declare themselves via `manifest.py` (AppHelper). The framework reads this at startup and auto-generates everything else.

### All app installation methods (any arasCore change must not break these):
1. **CLI + YAML/JSON**: `flask aras install-app ./app.yaml --activate` → creates DB records (AppManagerApp/Table/Column) + folders
2. **Web UI file upload**: `POST /admin/apps/install` → same as above, from browser
3. **CLI + manifest name**: `flask aras install-app soc` → imports `aras/app_soc/manifest.py`, syncs to DB via `sync_helper_to_db()`
4. **Web UI manifest install**: `POST /admin/apps/install-manifest/<app_name>` → same as above, from browser

### The golden rule: framework must know EVERY URL and endpoint
- **CRUD resource**: `ResourceDef(name, model)` → framework auto-generates `/api/<app>/<name>/` + `/admin/<app>/<name>/`
- **Non-CRUD API endpoint**: `CustomRoute(path, handler)` → mounted at `/api/<app>/<path>/`
- **Menu link to existing route (no new CRUD)**: `ResourceDef(name, url="/existing/route", menu_title="...", menu_icon="...")` with no `model` — framework skips route gen, shows link in menu only
- **Never** add `@app.route()` or `blueprint.add_url_rule()` outside the framework primitives (ResourceDef / CustomRoute).

### What arasCore auto-generates — write ZERO app code for these:
- REST API: `GET/POST /api/<app>/<resource>/` and `GET/PUT/DELETE /api/<app>/<resource>/<id>/`
- Admin list/add/edit/delete views: `/admin/<app>/<resource>/` and sub-paths
- Admin home: `/admin/<app>/`, settings: `/admin/<app>/settings/`, group pages: `/admin/<app>/<group_slug>/` where `group_slug` = MenuGroup title lowercased + spaces→hyphens (e.g. `MenuGroup("arasPos")` → `/admin/erp/araspot/`)
- Sidebar menu, WTForms forms (from model columns), RBAC checks on every API call

### Before editing arasCore/:
1. Understand how it affects BOTH code-based (manifest) AND dynamic (DB-based) apps
2. Understand how it affects ALL 4 install paths
3. If unsure → ask permission first

---

## Architecture
ERPNext-like ERP, simpler. Dynamic app registry engine — apps defined in `manifest.py` or DB (`AppManagerApp`), mounted at runtime via blueprints. Entry point: `arasCore/__init__.py` → `create_app()`.

Startup flow: extensions → blueprints → dynamic apps → API → jinja

## Key Files

### arasCore/arasAdmin/routes/ — SPLIT PACKAGE (was routes.py, NEVER read in full)
`routes.py` has been split into a package. `routes_legacy.py` is the old file (kept for reference, not imported).
`arasAdmin/__init__.py` imports `routes` which now resolves to the package.

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

### arasCore/arasAdmin/services.py — NEVER read in full (~1300 lines)
Functions only (no classes). Read by line number only.
Now also emits `emit_crud()` on admin form create/update/delete (4.4).
Snapshots `layout_json` per table and passes `layout_tabs` to form views (4.1).

| Function | Line | Purpose |
|---|---|---|
| `_make_sa_column` | L20 | internal helper |
| `_make_wtf_field` | L61 | internal helper |
| `clear_cache` | L140 | clear registry cache |
| `make_table_model(tbl, app_name, all_tables_in_app=None)` | L150 | generate SQLAlchemy model from AppManagerTable + Column |
| `make_table_form(tbl, model_cls, app_id)` | L212 | generate WTForm from metadata |
| `get_view_columns(tbl)` | L242 | columns shown in list view |
| `build_sidebar_menu()` | L253 | merge code-based (`_helper_registry`) + DB-based (`AppManagerApp`) menus |
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

Triggered by `GET /api/_search/?q=foo`. Cmd+K / Ctrl+K overlay in `adm_base.html`.

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


### aras/app_soc/manifest.py — NEVER read in full

| Function | Line | Purpose |
|---|---|---|
| `_handle_feed` | L12 | feed handler |
| `_handle_feed_public` | L26 | public feed handler |
| `_handle_friends_list` | L39 | friends list handler |
| `_handle_friend_request` | L51 | friend request handler |
| `_handle_search_users` | L63 | search users handler |

### arasCore/lib/blueprints.py — NEVER read in full

| Function | Line | Purpose |
|---|---|---|
| `get_helper_registry()` | L17 | return `_helper_registry` dict |
| `_load_manifest(pkg_name)` | L21 | import `app_*/manifest.py` |
| `_register_helper(flask_app, helper)` | L40 | mount routes from AppHelper |
| `_rbac_check(helper, res, action)` | L139 | RBAC permission check |
| `_mount_admin_resource(bp, res, adm_prefix, helper)` | L146 | mount admin resource route |
| `_is_app_enabled(entry, aras_pkg)` | L407 | check if app is active in DB or ARAS_AUTOLOAD |
| `_register_aras_apps(app)` | L443 | register all dynamic apps |
| `register_app_modules(app)` | L497 | entry — load all manifests + helpers |

### arasCore/__init__.py — NEVER read in full

| Function | Line | Purpose |
|---|---|---|
| `_read_mode_file()` | L13 | read mode config file |
| `create_app(config_type=None)` | L25 | entry point — full startup flow |

### arasCore/arasAdmin/models.py — NEVER read in full

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

### aras/app_erp/views/__init__.py — empty file, skip
### templates/admin/_menu_bar.html — HTML template, read only if directly relevant

## Do NOT Re-read
- `arasCore/auth.py` — use function table above
- `aras/app_soc/manifest.py` — use function table above
- `arasCore/lib/blueprints.py` — use function table above
- `arasCore/lib/base_model.py` — ArasModel + ArasSoftModel only
- `arasCore/__init__.py` — use function table above
- `arasCore/arasAdmin/models.py` — use class table above
- `aras/app_erp/views/__init__.py` — empty file
- `templates/admin/_menu_bar.html` — read only if directly relevant
- `arasCore/arasAdmin/routes_legacy.py` — old flat routes file, superseded by routes/ package, do not read
- `arasCore/arasAdmin/routes/apps.py` — use the function table above, read by line number only
- `arasCore/arasAdmin/routes/settings.py` — use the function table above, read by line number only
- `arasCore/lib/installer.py` — use the function table above, read by line number only
- `arasCore/lib/cli.py` — use the function table above, read by line number only
- `arasCore/arasAdmin/services.py` — use the function table above, read by line number only
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
