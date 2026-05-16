 Here is Claude's plan:      
 
# Plan: Framework List View Standardization + Template Rename + Per-User Column Persistence

## Context
Three interleaved tasks:
1. **Rename all `templates/admin/` files** to a consistent `adm_` / `adm_cfg_` / `adm_auth_` prefix scheme.
2. **Delete dead templates** (`templates/app_manager/` is entirely unused).
3. **Promote `ErpListViewSetting`** from `aras/erp/` to `arasCore` as `ListViewSetting`, persist column
   visibility per-user, and let apps declare extra toolbar buttons via `ResourceDef.extra_buttons`.

---

## Part A — Template Rename

### Naming Rules
| Prefix | Meaning |
|--------|---------|
| `adm_` | General admin page (layout wrapper, list, form, dashboard) |
| `adm_cfg_` | Framework config / settings (App Manager, tables, columns, schema migrations, DB inspector) |
| `adm_auth_` | Auth / user management pages |
| `adm_dev_` | Developer tools |
| `_list_partial.html` | Stays — underscore prefix = includeable partial |
| `base_*` | Stays — layout primitives |

### Rename Map

| Current | New | Notes |
|---------|-----|-------|
| `aras_list.html` | `gen_view_list.html` | |
| `aras_admin_form.html` | `gen_view_form.html` | |
| `dashboard.html` | `adm_dashboard.html` | |
| `messages.html` | `adm_messages.html` | |
| `send_message.html` | `adm_send_message.html` | |
| `apps.html` | `adm_cfg_apps.html` | |
| `app_form.html` | `adm_cfg_app_form.html` | |
| `app_install.html` | `adm_cfg_app_install.html` | |
| `app_migrations.html` | `adm_cfg_migrations.html` | |
| `settings.html` | `adm_cfg_settings.html` | |
| `aras_admin_settings.html` | `adm_cfg_app_settings.html` | |
| `aras_admin_settings_section.html` | `adm_cfg_settings_section.html` | |
| `aras_admin_tables.html` | `adm_cfg_tables.html` | custom row actions — cannot use gen_view_list |
| `aras_admin_table_form.html` | `adm_cfg_table_form.html` | form page, not a list |
| `aras_admin_columns.html` | `adm_cfg_columns.html` | dual-panel editor — cannot use gen_view_list |
| `db_table_detail.html` | `adm_cfg_db_detail.html` | raw DB schema view — not ORM-backed |
| `users.html` | `adm_auth_users.html` | |
| `user_form.html` | `adm_auth_user_form.html` | |
| `user_profile.html` | `adm_auth_user_profile.html` | |
| `user_log.html` | `adm_auth_user_log.html` | |
| `role_edit.html` | `adm_auth_role_edit.html` | |
| `dev.html` | `adm_dev.html` | |
| `dev_msg.html` | `adm_dev_msg.html` | |

**Already correct (no rename):** `base_index.html`, `adm_index.html`, `adm_app_home.html`,
`_list_partial.html`, all `base_*` partials.

### Delete
- `templates/app_manager/` — entire folder (confirmed zero Python references, dead code)

### App-level custom template folder convention
When an app needs many custom templates → use `templates/admin/app_<name>/` subfolder.
App-specific settings pages stay at `/admin/<app>/settings/` (framework-generated), no new route scope needed.

### Execution
- `git mv` each file (preserves history)
- Update every `render_template(...)` string in Python and `{% extends %}`/`{% include %}` in Jinja
- Files to update: `arasCore/admin/routes/*.py`, `arasCore/admin/services.py`,
  `arasCore/lib/admin_mount.py`, `arasCore/lib/blueprints.py`, all templates that reference renamed files

---

## Part B — Framework-Level ListViewSetting

### Step B1 — Add `ListViewSetting` to `arasCore/admin/models.py`

Append after last class:
```python
class ListViewSetting(ArasModel):
    __tablename__ = "gen_view_list_view_setting"
    __table_args__ = (
        db.UniqueConstraint("user_id", "doctype", name="uq_gen_view_list_view"),
    )
    user_id      = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    doctype      = db.Column(db.String(120), nullable=False)
    columns_json = db.Column(db.Text, nullable=True)   # JSON list of visible field names
    page_size    = db.Column(db.Integer, default=20, nullable=False)
    view_mode    = db.Column(db.String(10), default="list", nullable=False)
    show_totals  = db.Column(db.Boolean, default=False, nullable=False)
```

### Step B2 — Migration `m005_list_view_setting.py`

New file `arasCore/lib/migrations/m005_list_view_setting.py`.
Pattern: CREATE TABLE `gen_view_list_view_setting` with IF NOT EXISTS guard (same as m004).

### Step B3 — Replace `ErpListViewSetting` in `services.py` L754–783

Replace both `try: from aras.erp...` blocks with:
```python
from arasCore.admin.models import ListViewSetting
user_setting = ListViewSetting.query.filter_by(
    user_id=current_user.id, doctype=_doctype_key
).first()
```
Also read `columns_json` and pass as `saved_columns` to template.

### Step B4 — API endpoint `POST /admin/api/list-pref/`

```
POST /admin/api/list-pref/
Body JSON: {doctype: str, columns: [str, ...]}
```
Upserts `ListViewSetting` for current user. Returns `{"ok": true}`.
Add to `arasCore/admin/routes/settings.py`, register in `routes/__init__.py`.

### Step B5 — Persist column toggle in `_list_partial.html`

1. Add `data-field="{{ field }}"` to each column checkbox.
2. After toggling display, `fetch POST` to `/admin/api/list-pref/` with visible field names.
3. On page load: if `saved_columns` Jinja var is set, apply `display:none` to hidden columns.

---

## Part C — `extra_buttons` via `ResourceDef`

### Step C1 — Add field to `ResourceDef` (`arasCore/lib/app_helper.py` L138)

```python
extra_buttons: list = field(default_factory=list)
# [{"label": "Install", "url": "/admin/apps/install", "icon": "fa-upload", "style": "outline"}]
```

### Step C2 — Pass through `admin_mount.py:make_list()` (~L183)

```python
extra_buttons=res.extra_buttons or [],
```

### Step C3 — Declare for App Manager in settings route

```python
apps_extra_buttons = [
    {"label": "Install App", "url": url_for("admin.apps_install"), "icon": "fa-upload", "style": "outline"},
    {"label": "New App",     "url": url_for("admin.apps_new"),     "icon": "fa-plus",   "style": "primary"},
]
```
In `adm_cfg_settings.html` Apps panel: `{% set extra_buttons = apps_extra_buttons %}` before include.

### Step C4 — Alias `ErpListViewSetting` in `erp`

`aras/erp/erp_core/models/list_view.py`:
```python
from arasCore.admin.models import ListViewSetting as ErpListViewSetting  # noqa: F401
```
`ErpReportSetting` stays as-is.

---

## Critical Files

| File | Change |
|------|--------|
| `templates/admin/*.html` (23 files) | Rename per map above |
| `templates/app_manager/` | Delete entirely |
| `arasCore/admin/routes/*.py` + `services.py` + `admin_mount.py` | Update template string references |
| `arasCore/admin/models.py` | Add `ListViewSetting` |
| `arasCore/lib/migrations/m005_list_view_setting.py` | New — CREATE TABLE |
| `arasCore/admin/services.py` L754–783 | Replace `ErpListViewSetting` → `ListViewSetting`; pass `saved_columns` |
| `arasCore/lib/admin_mount.py` L183–195 | Pass `extra_buttons`, `saved_columns` |
| `arasCore/lib/app_helper.py` L138 | Add `extra_buttons` to `ResourceDef` |
| `arasCore/admin/routes/settings.py` | Add list-pref endpoint + `apps_extra_buttons` |
| `templates/admin/_list_partial.html` | `data-field` on checkboxes; fetch POST on toggle; restore on load |
| `aras/erp/erp_core/models/list_view.py` | Alias `ErpListViewSetting` |

---

## Verification

1. App still boots, no 500 on any admin page
2. `gen_view_list_view_setting` table created in DB
3. Toggle column off on any list → reload → column still hidden (persisted)
4. Settings page → Apps panel → Install App + New App buttons in toolbar
5. `ResourceDef(extra_buttons=[...])` in a manifest → buttons appear in that resource's list
6. `from aras.erp.erp_core.models.list_view import ErpListViewSetting` still works (alias)
