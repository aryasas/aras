 Here is Claude's plan:                                                                                                                                                                                 
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
 Plan: Framework Robustness, Genericness, Code Beauty & Dynamism Upgrades

 Context

 User wants to know what we can add to arasCore to make it more robust, generic, beautiful, and dynamic. This is an ideation + prioritization plan, not a single-feature plan. The framework already
 has strong bones:

 - AppHelper / ResourceDef / MenuGroup / CustomRoute / SubHandler (manifest DSL)
 - Universal REST API registry (api_handler.py)
 - Auto-mounted admin CRUD, home, settings, group pages
 - ArasModel / ArasSoftModel with hooks + to_dict()
 - ArasForm + build_form_from_table() (dynamic WTForm from DB)
 - Dynamic app registry (AppManagerApp/Table/Column) + YAML/JSON installer
 - Lightweight audit log (audit.py) opt-in per table
 - Page actions decorator registry

 After reading cached copies of app_helper.py, blueprints.py, api_handler.py, base_model.py, database.py, forms.py, audit.py, plus function tables in CLAUDE.md (routes/services/installer/cli), I see
 clear gaps in: query DSL, serialization, API ergonomics, caching, permissions wiring, form rendering, developer feedback, and the manifest surface.

 Below is a prioritized list of additions. Each entry is scoped so it can be picked up as a standalone follow-up task.

 ---
 Tier 1 — High leverage, low cost (ship first)

 1.1 ArasQuery — uniform list/filter/paginate/sort helper

 File: new arasCore/lib/query.py
 Why: blueprints.py make_list() + api_handler.py api_collection() + services.py each reinvent list logic (search, filter, order, pagination). Today the API /api/<app>/<resource>/ returns all rows
 unpaginated — that's a latent prod bug.
 What: One helper that takes (model, request.args) and returns (items, meta) with:
 - ?page=1&per_page=50 (default 50, max 500)
 - ?sort=-created_at,name (multi-sort, - = desc)
 - ?q=foo (full-text-ish over searchable cols)
 - ?filter[field]=value&filter[field__gte]=10 (operators: eq, ne, gte, lte, like, in)
 - ?fields=id,name,email (sparse fieldsets)

 Refactor api_collection() + make_list() to use it. Response envelope: {"data": [...], "meta": {"page", "per_page", "total", "total_pages"}}.

 1.2 Standard JSON error envelope + problem+json

 File: arasCore/lib/api_handler.py + arasCore/lib/error_handler.py
 Why: Currently returns {"error": str(ex)} with 500 for any exception — leaks stack traces, can't be parsed by clients.
 What: One helper api_error(status, code, message, details=None) → {"error": {"code": "VALIDATION", "message": "...", "details": {...}}}. Map ValueError → 400, PermissionError → 403, LookupError →
 404, SQLAlchemyError.IntegrityError → 409. Stack traces only in DEBUG=True.

 1.3 Resource-level schema endpoint

 File: arasCore/lib/api_handler.py
 Why: Frontends (and the admin form renderer) ask "what fields does /api/erp/acc/journal/ have?" — today they introspect by hand.
 What: GET /api/<app>/<resource>/_schema/ → JSON description of columns (name, type, required, relation target, choices, max_length). Reuse _sa_col_label and _sa_column_to_def already in
 installer.py.

 1.4 ResourceDef.filters + ResourceDef.searchable

 File: arasCore/lib/app_helper.py
 Why: Today list_columns exists but filter/search config for admin list view is inferred opportunistically. Make it declarative.
 What: Add filters: list[str] = [] (fields that can be filter targets) and searchable: list[str] = [] (fields indexed in the q= search). ArasQuery honors these.

 1.5 Beautify _mount_admin_resource() — split into AdminResourceMounter

 File: arasCore/lib/blueprints.py L146–404
 Why: It's 250 lines of nested closures (make_list, make_add, make_edit, make_delete, _make_form) with 10+ shadowed kwargs-defaults. Hard to read, hard to extend. This is the #1 ugly spot in the
 framework.
 What: Extract to arasCore/lib/admin_mount.py as a small class with methods, using module-level helpers for form building, FK map building, child table resolution. Net effect:
 blueprints._register_helper drops from ~130 lines to ~40.

 ---
 Tier 2 — Developer ergonomics (ship next)

 2.1 SubHandler lifecycle expansion

 File: arasCore/lib/app_helper.py L48
 Why: Current hooks miss common needs: field-level validation, bulk ops, export.
 What: Add validate(data, obj) (called before both create/update), before_list(query, request) (richer than list(query) alone — sees filters), export(queryset, fmt) (default CSV). Back-compat: keep
 existing names.

 2.2 Permission-aware to_dict()

 File: arasCore/lib/base_model.py
 Why: Same serializer runs for admin + public API; sensitive columns leak.
 What: __serialize_exclude__: set and __serialize_admin_only__: set (dropped unless current_user.is_admin). Opt-in, default empty — zero impact on existing models.

 2.3 @route / @action decorators on SubHandler

 File: arasCore/lib/app_helper.py
 Why: Today custom non-CRUD endpoints go in custom_routes=[CustomRoute(...)] — verbose, separated from the handler class. ERPNext-style actions (@whitelist) are more natural.
 What:
 class JournalHandler(SubHandler):
     @action(methods=["POST"])
     def post_journal(self, obj): ...          # POST /api/erp/acc/journal/<id>/post_journal/

     @route("/summary", methods=["GET"])
     def summary(self): ...                    # GET /api/erp/acc/journal/summary/
 Framework scans handler class at registration time. CustomRoute stays as escape hatch.

 2.4 Field DSL for ResourceDef.list_columns

 File: arasCore/lib/app_helper.py
 Why: list_columns=[("Label","field_name")] can't specify formatter, link, width, align.
 What:
 list_columns = [
     Field("name", label="Name", link=True, width="200px"),
     Field("total", label="Total", fmt="currency", align="right"),
     Field("status", badge={"paid": "success", "draft": "secondary"}),
 ]
 Back-compat: tuples still accepted, wrapped into Field(...).

 2.5 Frappe-style "report" primitive

 File: new arasCore/lib/reports.py
 Why: ERP apps (see aras/app_erp/erp_core/services/report_runner.py in cache) already need ad-hoc reports. No framework primitive exists.
 What: ReportDef(name, query_fn, columns, filters, chart=None) on AppHelper; framework mounts /admin/<app>/reports/<name>/ with a generic table + export button. Leverages ArasQuery.

 ---
 Tier 3 — Robustness & correctness

 3.1 Unified transaction wrapper

 File: new arasCore/lib/tx.py
 Why: api_handler.py, blueprints.py, services.py all have try/commit/except rollback copies — easy to miss one branch.
 What: with tx() as t: t.add(obj); ... context manager that commits on success, rolls back on any exception, routes exception to api_error or flash. Replace hand-written try/except in ~12 spots.

 3.2 Registry cache invalidation

 File: arasCore/arasAdmin/services.py (clear_cache L140)
 Why: Dynamic apps cache built models; when an admin edits a column, cache isn't always flushed — stale form field.
 What: Signal-based: emit resource_changed(app, table) from installer/column-edit routes → subscribers in services, audit, api_handler drop their caches. Small implementation, big reliability win.

 3.3 Startup health check + /admin/_health

 File: new arasCore/lib/health.py
 Why: Silent failures today: if mgr_table for an active app is missing columns, make_table_model() fails at first request, not at boot.
 What: At create_app() end, walk AppManagerApp(is_active=True) → try build each model/form → log summary. Expose /admin/_health JSON for monitoring.

 3.4 Schema migration runner for dynamic apps

 File: arasCore/lib/installer.py + arasCore/lib/migrations/
 Why: Column add works; column type-change or rename does not — the framework relies on db.create_all() which only creates missing tables.
 What: Per-dynamic-app migrations table (ab_<app>_migrations), diff between AppManagerColumn snapshot and live table (via SQLAlchemy inspector), generate ALTER TABLE stubs. First version: log-only +
 require manual approval; later: auto-apply for safe ops (add column nullable).

 3.5 Replace god-file arasCore/arasAdmin/routes.py (1288 lines)

 File: arasCore/arasAdmin/routes.py
 Why: CLAUDE.md already flags this as "never read in full". 42 view functions in one file.
 What: Split into routes/apps.py (install/activate/export), routes/users.py, routes/settings.py, routes/dev.py, routes/dashboard.py. Register them from arasAdmin/__init__.py. Pure refactor — no
 behavior change.

 ---
 Tier 4 — Dynamism (surface-level, user-visible)

 4.1 Layout DSL per page type

 File: AppManagerTable + templates/admin/ab_form.html
 Why: Today every form renders fields top-to-bottom. Frappe-style layouts (tabs, sections, column breaks) are a major UX win.
 What: Add AppManagerTable.layout_json (list of dicts: {"type": "tab|section|column_break", "label": "...", "fields": [...]}). ArasForm.render_fields() returns grouped output. Template renders
 Bootstrap tabs/cards.

 4.2 Client-side list view enhancements (server-driven)

 File: templates/admin/ab_list.html + static JS
 Why: List view is server-rendered only — no column resize, no inline-edit, no saved views (even though AppManagerPageView model exists and is unused).
 What: Wire AppManagerPageView → "Save current filters as view" button; column show/hide popover; inline-edit for string/boolean cells hitting PUT /api/<app>/<resource>/<id>/.

 4.3 Global search (⌘K)

 File: new arasCore/lib/search.py + template overlay
 Why: Ten apps × ten resources → user hunts through sidebar.
 What: GET /api/_search/?q=foo iterates resources whose searchable=[...] is set, returns top 5 per resource. Overlay bound to Cmd+K.

 4.4 Webhook / event bus

 File: new arasCore/lib/events.py
 Why: Custom handlers chain by import; no clean way for app B to react to app A's create.
 What: Blinker-based pub/sub: signal("resource.created", app, resource).send(obj). Framework emits on every CRUD. Apps subscribe in manifest.py via helper.on("erp.acc/journal.created", handler).

 ---
 Recommended order of execution

 The cheap + high-impact cluster, in order:

 1. 1.1 ArasQuery (fixes unpaginated API; used by many others)
 2. 1.2 Error envelope (once, applied everywhere)
 3. 1.5 AdminResourceMounter refactor (beauty + unblocks future changes)
 4. 1.3 _schema endpoint + 1.4 filters/searchable (small, enables 4.2 and 4.3 later)
 5. 3.1 tx wrapper (removes duplication introduced until here)
 6. 3.3 health check (sanity net after the above refactors)
 7. Then pick from Tier 2/3/4 based on product direction.

 ---
 Critical files touched

 ┌─────────────────┬────────────────────┬────────────────────────────────────────────────────────────────────────────────────┐
 │      Tier       │        Area        │                                        File                                        │
 ├─────────────────┼────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
 │ 1.1 / 1.3 / 1.4 │ API + list query   │ arasCore/lib/api_handler.py, new arasCore/lib/query.py, arasCore/lib/app_helper.py │
 ├─────────────────┼────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
 │ 1.2             │ Error envelope     │ arasCore/lib/api_handler.py, arasCore/lib/error_handler.py                         │
 ├─────────────────┼────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
 │ 1.5 / 3.5       │ Refactor           │ arasCore/lib/blueprints.py L146–404, arasCore/arasAdmin/routes.py                  │
 ├─────────────────┼────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
 │ 2.1 / 2.3 / 2.4 │ Manifest DSL       │ arasCore/lib/app_helper.py                                                         │
 ├─────────────────┼────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
 │ 2.2             │ Serialization      │ arasCore/lib/base_model.py                                                         │
 ├─────────────────┼────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
 │ 2.5             │ Reports            │ new arasCore/lib/reports.py                                                        │
 ├─────────────────┼────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
 │ 3.1             │ Transactions       │ new arasCore/lib/tx.py                                                             │
 ├─────────────────┼────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
 │ 3.2             │ Cache              │ arasCore/arasAdmin/services.py L140                                                │
 ├─────────────────┼────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
 │ 3.3             │ Health             │ new arasCore/lib/health.py, arasCore/__init__.py L25                               │
 ├─────────────────┼────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
 │ 3.4             │ Dynamic migrations │ arasCore/lib/installer.py, arasCore/lib/migrations/                                │
 ├─────────────────┼────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
 │ 4.1             │ Layouts            │ arasCore/arasAdmin/models.py L85, templates/admin/ab_form.html                     │
 ├─────────────────┼────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
 │ 4.2             │ List UX            │ templates/admin/ab_list.html, arasCore/arasAdmin/models.py L316                    │
 ├─────────────────┼────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
 │ 4.3             │ Global search      │ new arasCore/lib/search.py                                                         │
 ├─────────────────┼────────────────────┼────────────────────────────────────────────────────────────────────────────────────┤
 │ 4.4             │ Events             │ new arasCore/lib/events.py                                                         │
 └─────────────────┴────────────────────┴────────────────────────────────────────────────────────────────────────────────────┘

 Verification pattern (applies to each ticket)

 1. flask run — no ImportError, existing routes still 200.
 2. Run existing app (app_soc, ERP) — no regression on sidebar, CRUD, list, form.
 3. New feature: exercise via curl /api/... + browser /admin/....
 4. Dynamic app round-trip: install a YAML → add column in admin → verify form/API/schema endpoint reflect it.

---

# Plan: Framework List View Standardization + Template Rename + Per-User Column Persistence

## Context
Three interleaved tasks:
1. **Rename all `templates/admin/` files** to a consistent `adm_` / `adm_cfg_` / `adm_auth_` prefix scheme.
2. **Delete dead templates** (`templates/app_manager/` is entirely unused).
3. **Promote `ErpListViewSetting`** from `aras/app_erp/` to `arasCore` as `ListViewSetting`, persist column
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
| `aras_list.html` | `adm_list.html` | |
| `aras_admin_form.html` | `adm_form.html` | |
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
| `aras_admin_tables.html` | `adm_cfg_tables.html` | custom row actions — cannot use adm_list |
| `aras_admin_table_form.html` | `adm_cfg_table_form.html` | form page, not a list |
| `aras_admin_columns.html` | `adm_cfg_columns.html` | dual-panel editor — cannot use adm_list |
| `db_table_detail.html` | `adm_cfg_db_detail.html` | raw DB schema view — not ORM-backed |
| `users.html` | `adm_auth_users.html` | |
| `user_form.html` | `adm_auth_user_form.html` | |
| `user_profile.html` | `adm_auth_user_profile.html` | |
| `user_log.html` | `adm_auth_user_log.html` | |
| `role_edit.html` | `adm_auth_role_edit.html` | |
| `dev.html` | `adm_dev.html` | |
| `dev_msg.html` | `adm_dev_msg.html` | |

**Already correct (no rename):** `adm_base.html`, `adm_index.html`, `adm_app_home.html`,
`_list_partial.html`, all `base_*` partials.

### Delete
- `templates/app_manager/` — entire folder (confirmed zero Python references, dead code)

### App-level custom template folder convention
When an app needs many custom templates → use `templates/admin/app_<name>/` subfolder.
App-specific settings pages stay at `/admin/<app>/settings/` (framework-generated), no new route scope needed.

### Execution
- `git mv` each file (preserves history)
- Update every `render_template(...)` string in Python and `{% extends %}`/`{% include %}` in Jinja
- Files to update: `arasCore/arasAdmin/routes/*.py`, `arasCore/arasAdmin/services.py`,
  `arasCore/lib/admin_mount.py`, `arasCore/lib/blueprints.py`, all templates that reference renamed files

---

## Part B — Framework-Level ListViewSetting

### Step B1 — Add `ListViewSetting` to `arasCore/arasAdmin/models.py`

Append after last class:
```python
class ListViewSetting(ArasModel):
    __tablename__ = "adm_list_view_setting"
    __table_args__ = (
        db.UniqueConstraint("user_id", "doctype", name="uq_adm_list_view"),
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
Pattern: CREATE TABLE `adm_list_view_setting` with IF NOT EXISTS guard (same as m004).

### Step B3 — Replace `ErpListViewSetting` in `services.py` L754–783

Replace both `try: from aras.app_erp...` blocks with:
```python
from arasCore.arasAdmin.models import ListViewSetting
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
Add to `arasCore/arasAdmin/routes/settings.py`, register in `routes/__init__.py`.

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

### Step C4 — Alias `ErpListViewSetting` in `app_erp`

`aras/app_erp/erp_core/models/list_view.py`:
```python
from arasCore.arasAdmin.models import ListViewSetting as ErpListViewSetting  # noqa: F401
```
`ErpReportSetting` stays as-is.

---

## Critical Files

| File | Change |
|------|--------|
| `templates/admin/*.html` (23 files) | Rename per map above |
| `templates/app_manager/` | Delete entirely |
| `arasCore/arasAdmin/routes/*.py` + `services.py` + `admin_mount.py` | Update template string references |
| `arasCore/arasAdmin/models.py` | Add `ListViewSetting` |
| `arasCore/lib/migrations/m005_list_view_setting.py` | New — CREATE TABLE |
| `arasCore/arasAdmin/services.py` L754–783 | Replace `ErpListViewSetting` → `ListViewSetting`; pass `saved_columns` |
| `arasCore/lib/admin_mount.py` L183–195 | Pass `extra_buttons`, `saved_columns` |
| `arasCore/lib/app_helper.py` L138 | Add `extra_buttons` to `ResourceDef` |
| `arasCore/arasAdmin/routes/settings.py` | Add list-pref endpoint + `apps_extra_buttons` |
| `templates/admin/_list_partial.html` | `data-field` on checkboxes; fetch POST on toggle; restore on load |
| `aras/app_erp/erp_core/models/list_view.py` | Alias `ErpListViewSetting` |

---

## Verification

1. App still boots, no 500 on any admin page
2. `adm_list_view_setting` table created in DB
3. Toggle column off on any list → reload → column still hidden (persisted)
4. Settings page → Apps panel → Install App + New App buttons in toolbar
5. `ResourceDef(extra_buttons=[...])` in a manifest → buttons appear in that resource's list
6. `from aras.app_erp.erp_core.models.list_view import ErpListViewSetting` still works (alias)
