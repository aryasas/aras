# Project Context for Claude Code

## Project Instructions
- Report only at the end, briefly. No explanations during task execution.
- Follow the correct framework flow (SEE docs/MAIN.md).
- This app is similar to ERPNext in function and system but simpler. See ERPNext code in `erpnext-develop/`.
- Before hitting limit, stop and update `docs/progress.md`.
- Use English for all comments in code.
- DONT answering in every task. Just do task and report in the end.

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

### arasCore/arasAdmin/routes.py — NEVER read in full (1006 lines)
All routes are under the `arasAdmin` blueprint.

| Function | Line | Purpose |
|---|---|---|
| `before_request` | L19 | auth gate for all admin routes |
| `dashboard` | L31 | main dashboard |
| `dev` | L67 | dev tools page |
| `notifications` | L123 | notifications by category |
| `user_log` | L145 | user activity log |
| `settings` | L162 | site settings |
| `db_generate_view` | L230 | generate DB view |
| `server_settings_save` | L264 | save server settings |
| `server_restart` | L290 | restart server |
| `apps` | L301 | list all apps |
| `apps_new` | L316 | create new app |
| `apps_edit(app_id)` | L355 | edit app metadata |
| `apps_activate(app_id)` | L394 | activate app |
| `apps_deactivate(app_id)` | L412 | deactivate app |
| `apps_delete(app_id)` | L425 | delete app |
| `apps_tables(app_id)` | L443 | list tables for app |
| `apps_table_new(app_id)` | L458 | create new table |
| `apps_table_edit(app_id, table_id)` | L500 | edit table |
| `apps_table_delete(app_id, table_id)` | L542 | delete table |
| `apps_columns(app_id, table_id)` | L559 | list columns for table |
| `apps_column_delete(app_id, table_id, col_id)` | L618 | delete column |
| `apps_column_edit(app_id, table_id, col_id)` | L633 | edit column |
| `apps_fields(app_id)` | L665 | list fields for app |
| `apps_field_delete(app_id, field_id)` | L671 | delete field |
| `users` | L679 | list users |
| `users_new` | L691 | create user |
| `user_activate(user_id)` | L710 | activate user |
| `user_deactivate(user_id)` | L721 | deactivate user |
| `user_toggle_admin(user_id)` | L735 | toggle admin role |
| `users_export_csv` | L750 | export users to CSV |
| `apps_install` | L823 | install app from file |
| `apps_install_manifest(app_name)` | L878 | install from manifest |
| `apps_sync(app_id)` | L914 | sync app definition |
| `apps_template_yaml` | L956 | download YAML template |
| `apps_template_json` | L970 | download JSON template |
| `apps_export_yaml(app_id)` | L984 | export app as YAML |
| `apps_export_json(app_id)` | L1001 | export app as JSON |
| `_build_export_definition(app_obj)` | L1016 | internal — build export dict |

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

### arasCore/arasAdmin/services.py — NEVER read in full (733 lines)
Functions only (no classes). Read by line number only.

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

### arasCore/arasAdmin/models.py

| Class | Table | Purpose |
|---|---|---|
| `AppManagerApp` | `mgr_app` | app metadata |
| `AppManagerTable` | `mgr_table` | page type metadata |
| `AppManagerColumn` | `mgr_column` | custom field |
| `Message`, `Notification`, `UserActivity`, `Post` | — | admin built-ins |

### arasCore/auth.py
- `User` — table `auth_users`, login + password hash

### arasCore/lib/blueprints.py

| Function | Purpose |
|---|---|
| `_register_helper(flask_app, helper)` | mount routes from AppHelper |
| `_load_manifest(pkg_name)` | import `app_*/manifest.py` |
| `get_helper_registry()` | access `_helper_registry` for sidebar builder |

### arasCore/lib/api_handler.py

| Function | Purpose |
|---|---|
| `register_api_model(url_key, model, ...)` | register resource to universal REST API (`/api/<app>/<resource>/`) |
| `register_custom_route(...)` | register non-CRUD endpoint |

### arasCore/__init__.py
- `create_app()` — entry point, startup flow: extensions → blueprints → dynamic apps → API → jinja

## Do NOT Re-read
- `arasCore/arasAdmin/routes.py` — use the function table above, read by line number only
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

### arasCore/lib/base_model.py — read only if needed

| Class | Purpose |
|---|---|
| `ArasModel` | Base: id, is_active, created_at, updated_at, created_by_id, updated_by_id |
| `ArasSoftModel` | ArasModel + deleted_at, __soft_delete__ flag |

Import: `from arasCore.lib.base_model import ArasModel, ArasSoftModel, db`

## Common Commands
<!-- Add your build, test, lint commands here e.g.: -->
<!-- flask run, pytest, flask db migrate -->

## Performance
- Do NOT use extended thinking or long reasoning chains
- Work directly — read, edit, verify, done
- No contemplating before simple tasks
