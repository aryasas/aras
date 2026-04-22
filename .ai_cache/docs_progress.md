# Aras Progress

## Session: 2026-04-22

### Template Cleanup

**Deleted unused admin templates (14 files):**
- `adm_form_upload.html`, `adm_home.html`, `adm_list.html`, `adm_list_detail.html`, `adm_list_dict.html`, `adm_list_dt.html`, `adm_list_search.html`
- `activities.html`, `edit_profile.html`, `test.html`, `user_popup.html`
- `_menu_app.html`, `_notif_messages.html`, `aras_admin_fields.html`

**Error pages consolidated (5 → 1):**
- Deleted `_page_error.html`, `page_401.html`, `page_403.html`, `page_404.html`, `page_500.html`
- Created single `templates/page_error.html` with `{% if error_code %}` blocks
- Updated `arasCore/lib/error_handler.py` to pass `error_code` variable

**Template generics:**
- Created `templates/admin/_admin_submenu.html` — shared App Manager breadcrumb nav partial
  - Used by `aras_admin_tables.html` (no leaf) and `aras_admin_table_form.html` (with `submenu_title=title`)
  - `aras_admin_columns.html` keeps its own block (has table-switcher slot)
- Merged `adm_group_home.html` into `adm_app_home.html` — discriminated by `back_url` variable
  - `home_service.py` both home views now render `admin/adm_app_home.html`

**CSS cleanup:**
- Moved inline `<style>` block from `aras_admin_columns.html` into `static/admin/assets/css/custom-css.css`
  - Rules: `#relation-options`, `#length-option`, `#select-options` display:none; `.col-settings-section`

---

### Plan Items 3.4 → 4.4 (2026-04-22)

**3.4 — Schema migration runner for dynamic apps**
- New `arasCore/lib/schema_migrator.py`: diffs `AppManagerColumn` vs live DB via SA inspector; queues `ALTER TABLE ADD COLUMN` stubs in `mgr_schema_migration`
- `apply_pending(app_id, safe_only=True)`: auto-applies add_column; leaves type-change/rename as pending
- New `arasCore/lib/migrations/m003_dynamic_app_migrations.py`: creates `mgr_schema_migration` table
- Admin routes (in `routes/apps.py`): `GET /admin/apps/<id>/migrations`, `POST .../apply`, `GET .../diff`
- New template `templates/admin/app_migrations.html`; "Migrations" button added to `aras_admin_tables.html`
- `routes/apps.py` calls `diff_app()` after column add to auto-queue new migrations

**3.5 — Split routes.py (1288 lines → 5 focused files)**
- Old `arasCore/arasAdmin/routes.py` → renamed `routes_legacy.py`
- New package `arasCore/arasAdmin/routes/`:
  - `__init__.py` — `before_app_request` hook + imports all sub-modules
  - `dashboard.py` — dashboard, notifications, user-log
  - `dev.py` — dev page
  - `settings.py` — settings, DB generate-view, upload save/test, server save/restart, roles CRUD
  - `users.py` — users list/new/activate/deactivate/toggle-admin/export-csv
  - `apps.py` — apps CRUD, tables, columns, schema migrations, install, sync, export
- `arasAdmin/__init__.py` unchanged — `from . import routes` now resolves to the package

**4.1 — Layout DSL per page type**
- New `arasCore/lib/layout.py`: `parse_layout(tbl, form)` parses `tbl.layout_json` → tab/section/column-break structure
- New `templates/admin/base_form_layout.html`: Bootstrap-style tab panes + multi-column sections
- `aras_admin_form.html`: uses `base_form_layout.html` when `layout_tabs` passed, falls back to flat `base_form_fields.html`
- `services.py _register_built_app`: snapshots `layout_json`; `make_adm_add`/`make_adm_edit` compute and pass `layout_tabs`

**4.2 — Client-side list view enhancements**
- `aras_list.html`: column show/hide popover (`.aras-col-toggle-wrap`) — checkbox per column, toggles `<td>` visibility
- Inline-edit: `td.js-inline-cell` double-click → `<input>`, blur/Enter saves via `PUT` to resource endpoint, Escape cancels
- CSS added to `custom-css.css`: `.aras-col-toggle-popover`, `.aras-col-toggle-item`, `.aras-inline-input`

**4.3 — Global search (⌘K)**
- New `arasCore/lib/search.py`: `global_search(q, user)` — searches `searchable=True` AppManagerColumns + manifest `ResourceDef.searchable`; returns `{app, resource, title, url, match}` per hit
- New API endpoint `GET /api/_search/?q=foo` in `api_handler.py`
- `adm_base.html`: Cmd+K / Ctrl+K overlay with debounced fetch, result list with app › resource breadcrumb

**4.4 — Webhook / event bus**
- New `arasCore/lib/events.py`: blinker-based pub/sub; graceful no-op when blinker unavailable
- `emit_crud(app, resource, action, obj)` wired into `api_handler.py` (POST/PUT/DELETE) and `services.py` (admin form create/update/delete)
- Public API: `on(name, handler)`, `emit(name, obj)`, `@listener(name)` decorator
- `blinker` added to `requirements.txt`
