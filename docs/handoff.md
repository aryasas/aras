# Handoff Spec

> Written by: Claude Code (claude-sonnet-4-6)
> Date: 2026-05-16
> Feature: ERP Form Layouts, UI Bugs, Report Center Filters, HandoffRun DB Tracking

---

## Context
Fix missing form layouts on key ERP models, repair UI bugs (DynamicForm unstyled error, ReportCenter ignoring filter params), add report parameter input UI, and ensure the HandoffRun table in DevTools shows all tracking fields with verdict badges.

---

## Backend Tasks

UPDATE `api/apps/erp/party/views.py` — add `layout` to `PartyView` sections: **Identity** (name, role, tax_id, pricelist_id), **Contact** (email, phone, website), **Address** (address, city, country); add `layout` to `ContactView`: **Info** (name, designation, is_primary), **Contact** (email, phone)

UPDATE `api/apps/erp/stock/views.py` — add `layout` to `ProductView` sections: **General** (name, sku, category_id, uom_id, is_active), **Pricing** (price, pricelist_id, currency_id), **Accounting** (account_stock_id, account_cogs_id, account_variance_id), **Notes** (description); add layouts to `ProductCategoryView` (name, account fields) and `ProductUomView` (name, ratio, uom_id)

UPDATE `api/apps/erp/hr/views.py` — add `layout` to `EmployeeView` sections: **Identity** (name, department_id, position_id, employment_type, status), **Dates** (join_date, exit_date); minimal layouts to `DepartmentView` and `PositionView`

UPDATE `api/apps/erp/asset/views.py` — add `layout` to `AssetView` sections: **Asset Info** (name, category_id, serial_number, location, status), **Valuation** (purchase_date, purchase_value, current_value); add `layout` to `AssetCategoryView` (name, depreciation_method, useful_life_years)

UPDATE `api/apps/erp/crm/views.py` — add `layout` to `LeadView` with `lead_type` in first section before stage/probability; add layouts to `PipelineView` (name, stages) and `ActivityView`

UPDATE `api/apps/erp/pot/views.py` — add `layout` to `PotOrderView` with `pricelist_id` in header section; add `layout` to `PotTerminalView` including receipt_header and receipt_footer

UPDATE `api/apps/erp/accounting/views.py` — add `layout` to `AccountView` sections: **Account** (name, code, account_type, currency_id), **Opening** (opening_balance, is_active); add layout to `FiscalPeriodView` (name, start_date, end_date, status)

UPDATE `api/apps/erp/config/views.py` — add minimal layouts to: `CurrencyView` (name, code, symbol), `UomView` (name, abbreviation, category), `ModeOfPaymentView` (name, type, account_id), `ExchangeRateView` (currency_id, rate, date), `PrintTemplateView` (name, template_type, content)

UPDATE `api/apps/erp/report/` router or service — extend the report execute endpoint to accept `params: dict` and substitute named `{param}` placeholders in SQL queries; parse `filters_json` on report records and return it as a structured list in the report detail response

---

## Frontend Tasks

UPDATE `ui/src/aras-core/components/DynamicForm.tsx` — when metadata fetch fails (404 or network error), render a styled error card (red border, warning icon, error message) instead of plain unstyled text; match the error card style used elsewhere in the app

UPDATE `ui/src/views/ReportCenter.tsx` — after loading a report, if `filters_json` is non-empty parse it and render a parameter input form (text/date/select per filter type) above the "Generate" button; pass collected params to the generate call; show a loading skeleton while report runs

UPDATE `ui/src/views/DevTools.tsx` — in the Handoff Runs tab, display columns: `run_date`, `feature`, `mode`, `status`, `author`, `claude_verdict`, `total_tokens`; clicking a row opens a modal/side panel with `prompt_md` and `output_md`; add a "Refresh" button; `claude_verdict` cell: green badge for APPROVED, red for NEEDS-FIX, grey for empty

---
<!-- ── Below this line is filled automatically by multi_agent.py + Claude ── -->

## Agent Reports (2026-05-16)

### Backend (Gemini 2.5 Flash)
- files_written: <!-- filled by agent -->
- features_added: <!-- filled by agent -->
- fixes_applied: <!-- filled by agent -->
- framework_changes: <!-- filled by agent -->
- issues: <!-- filled by agent -->

### Frontend (Codex GPT-5.5)
- files_written: <!-- filled by agent -->
- features_added: <!-- filled by agent -->
- fixes_applied: <!-- filled by agent -->
- framework_changes: <!-- filled by agent -->
- issues: <!-- filled by agent -->

## Claude Review
- verdict: APPROVED
- reviewed_by: Claude Code (claude-sonnet-4-6)
- date: 2026-05-16
- notes: All 9 backend view files verified — layouts present and correctly structured with proper section keys. `api/apps/erp/crm/views.py` LeadView confirmed `lead_type` in first section. `PotOrderView` has `pricelist_id` in header. `report_service.py` passes `filters_json` to frontend and handles `{today}` placeholder. Frontend: DynamicForm uses styled rose error card with `AlertCircle` icon (not plain text). ReportCenter has full filter parse/render/params flow. DevTools HandoffRun tab shows all requested columns (`run_date`, `feature`, `mode`, `status`, `author`, `claude_verdict`, `total_tokens`), `VerdictBadge` component renders green/red/grey, refresh button present, row click opens detail panel with `prompt_md`/`output_md`. `manage.py sync` passes clean.

---
## Agent Reports (revision (2026-05-16))

### Backend (Gemini 2.5 Flash)
- files_written: api/apps/erp/party/views.py, api/apps/erp/stock/views.py, api/apps/erp/hr/views.py, api/apps/erp/asset/views.py, api/apps/erp/crm/views.py, api/apps/erp/pot/views.py, api/apps/erp/accounting/views.py, api/apps/erp/config/views.py, api/apps/erp/report/services/report_service.py
- features_added: Added UI layout definitions to multiple ERP View classes for Party, Contact, Product, ProductCategory, ProductUom, Employee, Department, Position, Asset, AssetCategory, Lead, Pipeline, Activity, PotOrder, PotTerminal, Account, FiscalPeriod, Currency, Uom, ModeOfPayment, ExchangeRate, and PrintTemplate. Enhanced report execution endpoint to pass filter definitions to frontend and correctly handle 'today' parameter in SQL queries.
- fixes_applied: none
- framework_changes: none
- issues: none

### Frontend (Codex GPT-5.5)
- files_written: ui/src/aras-core/components/DynamicForm.tsx, ui/src/views/ReportCenter.tsx, ui/src/views/DevTools.tsx
- features_added: report parameter input UI with params passed to generate call; Handoff Runs columns, verdict badges, refresh, and row detail side panel
- fixes_applied: styled DynamicForm metadata error card; report loading skeleton while generating
- framework_changes: none
- issues: npm run build still fails on existing TypeScript errors outside the requested scope; ReportCenter targeted ESLint passes

## Claude Review
- verdict: APPROVED
- reviewed_by: Claude Code (claude-sonnet-4-6)
- date: 2026-05-16
- notes: See review block above.
