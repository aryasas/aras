# ERP_12 — Customize & Reporting (Replan)

## Context

Task-4 asked for 6 features in one go: fix Journal Entry 404, ERPNext-style "Customize" per list page (column picker, search, filter), generic Reporting (GUI + Jinja/Python/SQL/JSON/YAML), "Reports" link on every table view, and 4 sample reports (Sales Summary, Purchase Summary, Profit & Loss, POS Shift) — plus build a POS Shift feature that did not yet exist. GUI English, data Indonesia.

The implementation was partly done by a sub-agent that ran out of tokens. Current state is close but not runnable end-to-end: DB schema drift on `pos_session`, sequence + report data not seeded, and report_seed is never invoked from the seeder pipeline.

This plan lists **only what is missing** to reach a working, demoable state. No rewrites of what already works.

---

## Current State Audit

Verified via `inspect(db.engine)` and file reads on 2026-04-19.

### Code — already done
- `aras/app_erp/erp_core/models/list_view.py` — `ErpListViewSetting` present, exported from `models/__init__.py`.
- `aras/app_erp/erp_core/models/report.py` — `ErpReport`, `ErpReportFavorite` present, exported.
- `aras/app_erp/erp_core/services/report_runner.py` — `run_report()` with query / script / jinja runners (69 lines).
- `aras/app_erp/erp_core/report_seed.py` — 4 reports defined (sales_summary, purchase_summary, profit_loss, pos_shift). **Not wired into seed pipeline.**
- `aras/app_erp/views/core.py` (409 lines) — routes: `/acc/entry/<id>/`, `/api/list-view-setting/` (GET+POST), `/acc/sales-invoice/`, `/acc/purchase-invoice/`, `/acc/journal-entries/`, `/reports/`, `/reports/<id>/`, `/reports/<id>/data.json`, `/reports/<id>/export.csv`, `/reports/pos-shift/`, `/dashboard`. All wired via `app_bp`.
- `aras/app_erp/manifest.py` — `ErpReport` registered under "Reports" MenuGroup at order=4.
- Templates: `erp/_list_view.html`, `erp/acc/{journal_entry_detail,sales_invoice_list,purchase_invoice_list,journal_entries_list}.html`, `erp/reports/{index,run,pos_shift}.html`.
- `aras/app_erp/templates/erp/dashboard.html` — Reports + POS sections present.
- `aras/app_erp/erp_pos/services/order_service.py` — `open_session()` generates `shift_number` from `pos.shift` sequence; `pay_order()` auto-creates Sales Invoice.
- `aras/app_erp/erp_pos/models/terminal.py` — `PosSession.shift_number` column declared in model.
- `aras/app_erp/erp_core/seed.py` — `("pos.shift", "SHIFT", 5, "yearly")` added to `SEQUENCES`.

### DB / runtime — missing or broken
1. **`pos_session` table is missing the `shift_number` column** (model declares it, DB has not been altered). New POS session opens will crash.
2. **`core_sequence` is missing `pos.shift` row** — even though it's in `SEQUENCES`, `_seed_sequences` only inserts on empty; seed needs a re-run or targeted insert.
3. **`erp_report` has 0 rows** — `report_seed.py` is not referenced from `erp_core/seed.py` `run_seed()`, nor from any CLI command.
4. **No "Reports" button on list pages** — `_list_view.html` exists but the three existing list templates (`sales_invoice_list.html`, etc.) may not yet include a link to `/erp/reports/?module=<x>`. To verify during execution.
5. **manifest.py handler for ErpReport** — registered as generic `admin_list=True` (list/add/edit/delete only). A "Run" action (link to `/erp/reports/<id>/`) should appear on the admin list row, otherwise users must type the URL.

### Not verified (spot-check during execution)
- `views/__init__.py` imports `from . import core` — confirmed earlier. Reports blueprint registration ok.
- Whether `_list_view.html` is actually included by the three list templates.
- Whether the column-picker JS on `_list_view.html` calls `/api/list-view-setting/` correctly.

---

## Remaining Work

### 1. DB migrations (one-shot ALTER + seed top-up)
File to create: `aras/app_erp/erp_core/migrate_task4.py` (small idempotent script, not Alembic — project uses `db.create_all()` + manual ALTER per existing pattern).

- `ALTER TABLE pos_session ADD COLUMN shift_number VARCHAR(30) NULL` (guarded: check `information_schema.columns` first).
- `INSERT INTO core_sequence (company_id, code, prefix, padding, reset_period)` for `pos.shift` if missing.

### 2. Hook `report_seed` into the seed pipeline
Edit: `aras/app_erp/erp_core/seed.py`
- Import `from .report_seed import seed_reports` (function name to confirm by reading `report_seed.py` final lines).
- Call `seed_reports()` inside `run_seed()` after `_seed_settings()`.

If `report_seed.py` exposes only the `REPORTS` list with no function, wrap it: iterate `REPORTS`, upsert by `name`.

### 3. Verify & wire the "Reports" action on list pages
- Open `templates/erp/_list_view.html` and the three acc list templates; ensure a button: `<a href="/erp/reports/?module={{ module }}" class="btn btn-sm">Reports</a>` is rendered in the toolbar.
- If missing on the three acc templates, add a single line to each.

### 4. Admin list "Run" action for ErpReport
Edit: `aras/app_erp/manifest.py` and either a dedicated `ReportHandler` or template override.
- Simplest: override the list template for `erp/report` with a column that links to `/erp/reports/<id>/`. No manifest change needed if handler layer already supports a `row_actions` hook; otherwise add a small custom route `/admin/erp/report/<id>/run` that redirects to `/erp/reports/<id>/`.
- Pick whichever is least invasive after reading the current handler.

### 5. Smoke-test checklist (end-to-end)
Run `python run.py` then, as a logged-in admin:

- `GET /admin/erp/acc/entry/` → click an entry → expects `/erp/acc/entry/<id>/` to render detail (no 404).
- `GET /erp/acc/sales-invoice/?search=INV&date_from=2026-01-01` → list renders, filters apply.
- `GET /erp/acc/purchase-invoice/` → list renders.
- `GET /erp/acc/journal-entries/?state=posted` → list renders.
- `GET /erp/reports/` → 4 reports listed.
- `GET /erp/reports/1/` → Sales Summary form, run with date range, table shows rows.
- `GET /erp/reports/1/export.csv` → CSV downloads.
- `GET /erp/reports/pos-shift/` → dedicated report view.
- Open POS → `/erp/pos` → session opens without `Unknown column 'shift_number'` error.
- Column picker on one list page: `POST /api/list-view-setting/` with `{doctype:"acc_sales_invoice", columns:[...]}` → reload page → layout persists.

### 6. Update `docs/progress.md`
Per `CLAUDE.md` rule: before the next context limit, append a dated section summarizing what's now green and what remains.

---

## Critical Files

Read before editing:
- `aras/app_erp/erp_core/seed.py` — where to wire `report_seed`
- `aras/app_erp/erp_core/report_seed.py` — confirm entrypoint function
- `aras/app_erp/templates/erp/_list_view.html` — toolbar for Reports button
- `aras/app_erp/templates/erp/acc/{sales,purchase}_invoice_list.html`, `journal_entries_list.html` — verify toolbar include
- `aras/app_erp/manifest.py` — ReportHandler / admin row action decision
- `aras/app_erp/views/core.py` — current route surface (no change expected unless redirect route needed)

Write / create:
- `aras/app_erp/erp_core/migrate_task4.py` — ALTER + sequence insert
- `aras/app_erp/erp_core/seed.py` — 1 import + 1 call
- Possibly 3 templates (add Reports button line) — only if missing

## Out of scope (keep for later)
- YAML/JSON report definition files (code path exists in `report_runner.py` via `report_type`; no front-end editor yet).
- Role-based visibility per report.
- Saved-filter sharing across users.
- Full Alembic migration chain (this project still uses `db.create_all()` + targeted ALTERs).

## Verification summary
Run, in order: migrate_task4 → re-run `run_seed()` (or invoke `seed_reports()` directly) → restart app → walk the smoke-test checklist in section 5 → update `docs/progress.md`.
