# Aras Progress

## Session: 2026-04-24 — ERP Rename + Charge Refactor

### Remove `Core` prefix — model classes and DB tables

All `Core*` class names and `core_*` table names removed from app-level ERP code.

**Class renames:**
| Old | New | Table |
|-----|-----|-------|
| `CoreCompany` | `Company` | `company` |
| `CoreCurrency` | `Currency` | `currency` |
| `CoreFxRate` | `FxRate` | `fx_rate` |
| `CoreFiscalYear` | `FiscalYear` | `fiscal_year` |
| `CoreFiscalPeriod` | `FiscalPeriod` | `fiscal_period` |
| `CoreSequence` | `Sequence` | `sequence` |
| `CoreSetting` | `Setting` | `setting` |
| `CorePrintTemplate` | `PrintTemplate` | `print_template` |
| `CoreAttachment` | `Attachment` | `attachment` |
| `CoreAuditLog` | `AuditLog` | `audit_log` |
| `CoreNotification` | `ErpNotification` | `notification` |
| `CoreEmailTemplate` | `EmailTemplate` | `email_template` |
| `CoreRole` | `ErpRole` | `erp_role` |
| `CorePermission` | `ErpPermission` | `erp_permission` |
| `CoreRolePermission` | `ErpRolePermission` | `erp_role_permission` |
| `CoreUserCompany` | `ErpUserCompany` | `erp_user_company` |
| `CoreTax` | `Charge` | `charge` |
| `CoreTaxGroup` | deleted | — |

Note: `ErpRole`/`ErpPermission` use `erp_` prefix because arasCore already has `Role`/`Permission` classes. All other names are clean (no prefix conflicts).

### Tax → Charge refactor

- `core_tax` table → `charge` table; class `CoreTax` → `Charge`
- `core_tax_group` / `core_tax_group_line` dropped
- `CoreCharge.tax_type` → `Charge.charge_type`
- Invoice lines: removed single `tax_id`/`tax_amt` per line
- Added child tables `AccSalesInvoiceCharge` / `AccPurchaseInvoiceCharge` — invoices can now have **multiple charges**
- Invoice header: `tax_amt` → `charge_amt`
- `AccJournalLine.tax_id` → `charge_id`
- `AccAccount.tax_id_default` → `charge_id_default`

### Menu restructure

- "Core" MenuGroup → renamed to **"Settings"**
- `Company` moved into Settings (it's configuration, not a transaction entity)
- `FxRate`, `FiscalPeriod`, `CrmContact`, `CrmStage`, `CrmActivity`, `PosShiftEntry`, all stock sub-tables, all invoice line/charge tables → `admin_list=False, is_child_table=True` (hidden from menu)
- New manifest imports: `AccSalesInvoiceCharge`, `AccPurchaseInvoiceCharge`
- Removed: `CoreCustomField` import (unused), `CoreTaxGroup` ResourceDef

### Migration 005 (`migrations/005_rename_core_tables.py`)

Idempotent. Renames 18 tables, creates `acc_sales_invoice_charge`, `acc_purchase_invoice_charge`, drops `core_tax_group`/`core_tax_group_line`. Ran successfully.

### Files changed (28 + models)

`manifest.py`, all `erp_core/models/*.py`, `erp_acc/models/*.py`, `erp_crm/models/*.py`, `erp_pos/models/terminal.py`, `erp_stock/models/*.py`, `erp_core/seed.py`, `erp_core/decorators.py`, `erp_core/services/*.py`, `erp_acc/services/posting.py`, `erp_pos/services/pos_invoice.py`, `erp_pos/services/print_service.py`, `erp_stock/seed.py`, `views/core.py`, `views/pos.py`

---

## Session: 2026-04-23 — Planned (not yet executed)

### Template rename + ListViewSetting promotion (next task)

**Template naming convention adopted:**
- `adm_` — general admin page (list, form, dashboard, messages)
- `adm_cfg_` — framework config/settings (App Manager, tables, columns, migrations, DB inspector)
- `adm_auth_` — user/role management
- `adm_dev_` — developer tools
- `_list_partial.html`, `base_*` — keep as-is (partials / layout primitives)

**Rename map (23 files):**
- `aras_list.html` → `adm_list.html`
- `aras_admin_form.html` → `adm_form.html`
- `dashboard.html` → `adm_dashboard.html`
- `messages.html` → `adm_messages.html`
- `send_message.html` → `adm_send_message.html`
- `apps.html` → `adm_cfg_apps.html`
- `app_form.html` → `adm_cfg_app_form.html`
- `app_install.html` → `adm_cfg_app_install.html`
- `app_migrations.html` → `adm_cfg_migrations.html`
- `settings.html` → `adm_cfg_settings.html`
- `aras_admin_settings.html` → `adm_cfg_app_settings.html`
- `aras_admin_settings_section.html` → `adm_cfg_settings_section.html`
- `aras_admin_tables.html` → `adm_cfg_tables.html`
- `aras_admin_table_form.html` → `adm_cfg_table_form.html`
- `aras_admin_columns.html` → `adm_cfg_columns.html`
- `db_table_detail.html` → `adm_cfg_db_detail.html`
- `users.html` → `adm_auth_users.html`
- `user_form.html` → `adm_auth_user_form.html`
- `user_profile.html` → `adm_auth_user_profile.html`
- `user_log.html` → `adm_auth_user_log.html`
- `role_edit.html` → `adm_auth_role_edit.html`
- `dev.html` → `adm_dev.html`
- `dev_msg.html` → `adm_dev_msg.html`

**Delete:** `templates/app_manager/` — entire folder, confirmed zero Python references.

**App-level custom templates:** use `templates/admin/app_<name>/` subfolder when app needs many files.

**ListViewSetting (framework-level):**
- Add `ListViewSetting` model to `arasCore/arasAdmin/models.py` (table: `adm_list_view_setting`)
- Migration `m005_list_view_setting.py`
- Replace `ErpListViewSetting` imports in `services.py` with `ListViewSetting`; persist `columns_json`
- `aras/app_erp/erp_core/models/list_view.py` → alias `ErpListViewSetting = ListViewSetting`
- API endpoint `POST /admin/api/list-pref/` for JS to save column visibility
- `_list_partial.html` JS: POST on column toggle, restore on page load

**`ResourceDef.extra_buttons`:**
- Add `extra_buttons: list` field to `ResourceDef` in `arasCore/lib/app_helper.py`
- `admin_mount.py:make_list()` passes `extra_buttons` to template
- Settings route declares `apps_extra_buttons` (Install App + New App) for the Apps panel

---

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
