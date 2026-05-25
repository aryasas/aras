# Backend QA - Half B
## Summary
- critical: 1 | high: 5 | medium: 7 | low: 4

## Critical
- [api/apps/report/services/report_service.py:56] Query reports with raw SQL always fail: `_generate_query_report()` checks `report.script`, but executes `db.execute(text(script), params)` where `script` is undefined. Any SELECT-backed report returns `"SQL Error: name 'script' is not defined"`.

## High
- [api/apps/report/routers.py:12] Report endpoints `/api/v1/report/erp/report/profit-loss`, `/balance-sheet`, and `/trial-balance` have no `Depends(get_current_user)` and accept arbitrary `org_id`. They expose financial reporting data without RBAC or tenant/org scoping checks.
- [api/apps/dev/app.py:11] Custom developer-template routes have no auth dependency. `/api/v1/dev/dev_template_trees` and `/api/v1/dev/dev_template_annotations` can read/write developer metadata if the app router is mounted publicly.
- [api/apps/stock/app.py:14] Custom stock endpoint `/api/v1/stock/items/{item_id}/stock` has no `Depends(get_current_user)` and returns inventory quantities without auth.
- [api/apps/report/services/report_service.py:139] Script reports execute stored Python with `exec(report.script, ctx, ctx)`. This is high risk unless report creation/editing is strictly admin-only and scripts are trusted.
- [api/apps/saas/models.py:45] `Subscription.approve()` creates the portal user and setup link, but does not auto-issue a license token. `LicenseService.issue_license()`, `renew_license()`, and `revoke_license()` exist in `api/apps/saas/services/license_service.py`, so approval currently leaves the customer in trial without a token until a separate action runs. This may be intentional, but should be explicitly decided before production.

## Medium
- [api/apps/hr/app.py:1] HR has `DepartmentView`, `PositionView`, and `EmployeeView`, but `app.py` does not import `views` for side-effect registration and does not use `autodiscover_models`.
- [api/apps/party/app.py:1] Party has `PartyView` and `ContactView`, but `app.py` does not import `views` for side-effect registration and does not use `autodiscover_models`.
- [api/apps/notes/models.py:5] Notes defines `Note`, but there is no `api/apps/notes/views.py`. This violates the "View per model" convention.
- [api/apps/dev/models.py:8] Dev defines `HandoffRun` and `TemplateAnnotation`, but there is no `api/apps/dev/views.py`. The app also manually lists framework registry models rather than using autodiscovery.
- [api/apps/stock/views.py:1] Stock is missing explicit views for `ItemAccount` and `DeliveryNoteLine`. All other stock models have views.
- [api/apps/report/models.py:23] `Report.generate_report()` returns an `ok(...)` envelope, but the report router endpoints return raw service dictionaries rather than the framework envelope.
- [api/apps/report/services/report_service.py:80] Report generation catches broad `Exception` and returns stringified errors to users. This hides server-side defects and may leak internal details.

## Low
- [api/apps/report/seed_reports.py:356] Seed script uses `print()` instead of logger.
- [api/apps/seed_demo.py:425] Demo seed returns a plain dict summary. No hardcoded credentials, hardcoded tenant IDs, or prod-looking URLs were found in `api/apps/seeds/` or `api/apps/seed_demo.py`.
- [api/apps/base/document.py:21] `DocumentBase.note_id` references `erp_core_notes.id`; the scoped note model exists in `api/apps/core/models.py`, while a separate unscoped `notes_note` model also exists in `api/apps/notes/models.py`. This duplicate note concept is a drift risk.
- [api/apps/pot/routers.py:48] POT custom endpoints do use `ok(...)`/`err(...)` envelopes and `Depends(get_current_user)`, but helper functions do not enforce that the requested `session_id` belongs to a user-accessible organization beyond the session query itself.

## App Inventory
- `dev`: models `HandoffRun`, `TemplateAnnotation`; views none; routers `GET/POST /dev_template_trees`, `POST /dev_template_annotations`; services/seed helpers `seed_templates.py`.
- `hr`: models `Department`, `Position`, `Employee`; views `DepartmentView`, `PositionView`, `EmployeeView`; routers none; services none.
- `notes`: model `Note`; views none; routers none; services none.
- `party`: models `Party`, `Contact`; views `PartyView`, `ContactView`; routers none; services none.
- `pot`: models `PotTerminal`, `PotSession`; views `PotTerminalView`, `PotSessionView`; router `GET /sessions/{session_id}/items`, `POST /sessions/{session_id}/quick_invoice`; service `services/pot.py`.
- `report`: model `Report`; view `ReportView`; router `GET /erp/report/profit-loss`, `GET /erp/report/balance-sheet`, `GET /erp/report/trial-balance`; services `ReportService`, `FinanceReportService`.
- `stock`: models `ItemCategory`, `Item`, `ItemAccount`, `ItemUom`, `PriceList`, `PromoBundle`, `PromoBundleItem`, `Location`, `DeliveryNote`, `DeliveryNoteLine`, `StockMovement`, `StockMovementLine`, `ItemBundle`, `ItemLocation`; views exist except `ItemAccount` and `DeliveryNoteLine`; router `GET /items/{item_id}/stock`; services `account`, `coa_resolver`, `posting`, `price`, `promo`, `stock`, `uom`, `valuation`, `workflow`.

## ERP Base
- Present at `api/apps/base/`: `DocumentBase`, `LineItemBase`, `MasterDataBase`, and `ConfigBase` are intact and inherit through a single base chain from `ErpBase`.
- Inheriting models in the audited ERP apps declare exactly one base class among `DocumentBase`, `LineItemBase`, `MasterDataBase`, `ConfigBase`, or `ErpBase`.
- `DocumentBase` and `MasterDataBase` carry `__scoped_by__ = [("org_id", "erp_config_organizations")]`; `LineItemBase`, `ConfigBase`, and `ErpBase` do not.

## POS Endpoint Surface
- Generated CRUD/action endpoints exist for `/api/v1/pot/terminals` and `/api/v1/pot/sessions`.
- Custom endpoints exist:
- `GET /api/v1/pot/sessions/{session_id}/items` returns `ok(result)`.
- `POST /api/v1/pot/sessions/{session_id}/quick_invoice` returns `ok({...})` or `err(...)`.
- Session lifecycle model actions exist on `PotSession`: `open_pos`, `close_session`, and `shift_report`; generated routes are visible in the route audit output.

## Reports Endpoint Surface
- `/api/v1/report/erp/report/profit-loss`
- `/api/v1/report/erp/report/balance-sheet`
- `/api/v1/report/erp/report/trial-balance`
- `/api/v1/report/reports/{item_id}/action/generate_report`
- The three custom finance endpoints bypass RBAC and scoping. Generated model action auth depends on the framework router factory, but raw report scripts remain high-risk.

## Multi-Tenancy
- Sensitive unscoped models found in the grep:
- `api/apps/saas/models.py`: `Plan`, `Subscription`, `LicenseToken`, `ActivationRequest` have no `__scoped_by__`. `Subscription`, `LicenseToken`, and `ActivationRequest` are sensitive tenant/customer records.
- `api/core/auth/models.py` was outside the requested app grep output, but user records are framework auth records and should be checked separately for explicit tenant/org access semantics.
- `api/apps/dev/models.py`: `HandoffRun`, `TemplateAnnotation` have no `__scoped_by__`; they can contain prompts, run output, and template metadata.
- `api/apps/notes/models.py`: `Note` has no `__scoped_by__`, while ERP `DocumentBase.note_id` points to `erp_core_notes`.
- ERP master/document models inheriting `MasterDataBase`/`DocumentBase` are scoped. Line-item models generally rely on parent relationships; standalone `ErpBase` models need case-by-case scoping.

## Imports & collection output
Route audit command:
```text
cd api && python -c "from main import app; [print(getattr(r,'methods',''), getattr(r,'path','')) for r in app.routes]" 2>&1 | head -200
```

Output:
```text
{"levelname": "INFO", "asctime": "2026-05-25 18:03:01,653", "filename": "main.py", "lineno": 43, "process": 11688, "thread": 8513444032, "name": "main", "message": "Initializing database schema and running migrations..."}
{"levelname": "INFO", "asctime": "2026-05-25 18:03:02,072", "filename": "main.py", "lineno": 46, "process": 11688, "thread": 8513444032, "name": "main", "message": "Database schema and migrations complete."}
Discovering apps in apps...
Registered route: /api/v1/accounting/accounts
Registered route: /api/v1/accounting/fiscal-periods
Registered route: /api/v1/accounting/grn-lines
Registered route: /api/v1/accounting/grns
Registered route: /api/v1/accounting/inflow-invoices
Registered route: /api/v1/accounting/inflow-invoice-charges
Registered route: /api/v1/accounting/inflow-invoice-lines
Registered route: /api/v1/accounting/entries
Registered route: /api/v1/accounting/entry-lines
Registered route: /api/v1/accounting/outflow-invoices
Registered route: /api/v1/accounting/outflow-invoice-charges
Registered route: /api/v1/accounting/outflow-invoice-lines
Registered route: /api/v1/accounting/payments
Registered route: /api/v1/accounting/payment-allocations
Registered custom router for app accounting at prefix: /api/v1/accounting
Registered custom router for app accounting at prefix: /api/v1/accounting
Registered route: /api/v1/asset/categories
Registered route: /api/v1/asset/assets
Registered route: /api/v1/config/charges
Registered route: /api/v1/config/currencies
Registered route: /api/v1/config/exchange-rates
Registered route: /api/v1/config/payment-modes
Registered route: /api/v1/config/notifications
Registered route: /api/v1/config/organizations
Registered route: /api/v1/config/payment-accounts
Registered route: /api/v1/config/org-posting-rules
Registered route: /api/v1/config/org-vocabulary
Registered route: /api/v1/config/price-types
Registered route: /api/v1/config/print-templates
Registered route: /api/v1/config/settings
Registered route: /api/v1/config/uoms
Registered route: /api/v1/config/workflow-actions
Registered route: /api/v1/config/workflow-states
Registered route: /api/v1/config/workflow-templates
Registered route: /api/v1/config/workflow-transitions
Registered route: /api/v1/config/doc-series
Registered route: /api/v1/config/erp-user-access
Registered custom router for app config at prefix: /api/v1/config
Registered custom router for app config at prefix: /api/v1/config
Registered route: /api/v1/crm/leads
Registered route: /api/v1/crm/pipelines
Registered route: /api/v1/crm/stages
Registered route: /api/v1/crm/activities
Registered route: /api/v1/dev/aras-apps
Registered route: /api/v1/dev/aras-resources
Registered route: /api/v1/dev/aras-fields
Registered route: /api/v1/dev/aras-links
Registered route: /api/v1/dev/aras-activity-logs
Registered route: /api/v1/dev/auth-users
Registered route: /api/v1/dev/sys-settings
Registered route: /api/v1/dev/aras-widgets
Registered route: /api/v1/dev/aras-dashboard-layouts
Registered route: /api/v1/dev/handoff-runs
Registered route: /api/v1/dev/template-annotations
Registered custom router for app dev at prefix: /api/v1/dev
Registered route: /api/v1/hr/departments
Registered route: /api/v1/hr/positions
Registered route: /api/v1/hr/employees
Registered route: /api/v1/notes/note
Registered route: /api/v1/party/parties
Registered route: /api/v1/party/contacts
Registered route: /api/v1/pot/terminals
Registered route: /api/v1/pot/sessions
Registered custom router for app pot at prefix: /api/v1/pot
Registered route: /api/v1/report/reports
Registered custom router for app report at prefix: /api/v1/report
Registered route: /api/v1/saas/activation-request
Registered route: /api/v1/saas/license-token
Registered route: /api/v1/saas/plan
Registered route: /api/v1/saas/subscription
Registered custom router for app saas at prefix: /api/v1/saas
Registered route: /api/v1/stock/delivery-notes
Registered route: /api/v1/stock/delivery-note-lines
Registered route: /api/v1/stock/items
Registered route: /api/v1/stock/item-accounts
Registered route: /api/v1/stock/item-bundles
Registered route: /api/v1/stock/categories
Registered route: /api/v1/stock/item-locations
Registered route: /api/v1/stock/item-uoms
Registered route: /api/v1/stock/locations
Registered route: /api/v1/stock/pricelists
Registered route: /api/v1/stock/promo-bundles
Registered route: /api/v1/stock/promo-items
Registered route: /api/v1/stock/movements
Registered route: /api/v1/stock/movement-lines
Registered custom router for app stock at prefix: /api/v1/stock
Registered route: /api/v1/web/contact-submission
Registered route: /api/v1/web/landing-section
Registered route: /api/v1/web/site-setting
Registered route: /api/v1/web/menu-item
Registered route: /api/v1/web/page
Registered custom router for app web at prefix: /api/v1/web
{'GET', 'HEAD'} /openapi.json
{'GET', 'HEAD'} /docs
{'GET', 'HEAD'} /docs/oauth2-redirect
{'GET', 'HEAD'} /redoc
{'POST'} /api/v1/auth/token
{'GET'} /api/v1/auth/me
{'POST'} /api/v1/auth/change-password
{'POST'} /api/v1/auth/forgot-password
{'POST'} /api/v1/auth/reset-password
{'POST'} /api/v1/{resource_name}/query
{'GET'} /api/v1/search
{'GET'} /api/v1/handlers
{'GET'} /api/v1/{resource_name}/{item_id}/actions
{'POST'} /api/v1/{resource_name}/{item_id}/action/{action_name}
{'GET'} /api/v1/admin/apps
{'POST'} /api/v1/admin/install
{'DELETE'} /api/v1/admin/uninstall/{app_name}
{'GET'} /api/v1/admin/apps/capabilities
{'POST'} /api/v1/dev/dev_handoff_runs
{'GET'} /api/v1/dev/dev_handoff_runs
{'PATCH'} /api/v1/dev/dev_handoff_runs/{run_id}
{'POST'} /api/v1/dev/tasks/enqueue
{'GET'} /api/v1/dev/tasks/{task_id}/status
{'POST'} /api/v1/dev/sync
{'GET'} /api/v1/dev/info
{'GET'} /api/v1/dev/stats
{'GET'} /api/v1/dev/inspect/resource/{resource_name}
{'GET'} /api/v1/dev/inspect/models
{'GET'} /api/v1/dev/inspect/routes
{'GET'} /api/v1/dev/inspect/env
{'GET'} /api/v1/metadata/{resource_name:path}
{'GET'} /api/v1/models
{'GET'} /api/v1/schemas
{'GET'} /api/v1/views
{'POST'} /api/v1/files/upload
{'GET'} /api/v1/files/download/{filename}
{'GET'} /api/v1/dashboard/layouts
{'GET'} /api/v1/dashboard/layouts/{layout_id}
{'POST'} /api/v1/dashboard/layouts
{'PUT'} /api/v1/dashboard/layouts/{layout_id}
{'DELETE'} /api/v1/dashboard/layouts/{layout_id}
{'POST'} /api/v1/dashboard/layout
{'GET'} /api/v1/dashboard/widgets
{'GET'} /api/v1/tenants
{'POST'} /api/v1/tenants/provision
{'POST'} /api/v1/tenants/{tenant_id}/seed
{'DELETE'} /api/v1/tenants/{tenant_id}
 /api/v1/ws
{'GET'} /api/v1/sys_filters
{'POST'} /api/v1/sys_filters
{'DELETE'} /api/v1/sys_filters/{filter_id}
{'GET'} /api/v1/accounting/accounts/metadata
{'GET'} /api/v1/accounting/accounts/
{'GET'} /api/v1/accounting/accounts
{'GET'} /api/v1/accounting/accounts/aggregate
{'GET'} /api/v1/accounting/accounts/export
{'POST'} /api/v1/accounting/accounts/import
{'POST'} /api/v1/accounting/accounts/
{'POST'} /api/v1/accounting/accounts
{'GET'} /api/v1/accounting/accounts/deleted
{'POST'} /api/v1/accounting/accounts/{item_id}/restore
{'GET'} /api/v1/accounting/accounts/{item_id}/linked-documents
{'GET'} /api/v1/accounting/accounts/{item_id}
{'PUT'} /api/v1/accounting/accounts/{item_id}
{'PATCH'} /api/v1/accounting/accounts/{item_id}
{'DELETE'} /api/v1/accounting/accounts/{item_id}
{'POST'} /api/v1/accounting/accounts/bulk-delete
{'POST'} /api/v1/accounting/accounts/batch
{'POST'} /api/v1/accounting/accounts/{item_id}/action/reconcile
{'GET'} /api/v1/accounting/fiscal-periods/metadata
{'GET'} /api/v1/accounting/fiscal-periods/
{'GET'} /api/v1/accounting/fiscal-periods
{'GET'} /api/v1/accounting/fiscal-periods/aggregate
{'GET'} /api/v1/accounting/fiscal-periods/export
{'POST'} /api/v1/accounting/fiscal-periods/import
{'POST'} /api/v1/accounting/fiscal-periods/
{'POST'} /api/v1/accounting/fiscal-periods
{'GET'} /api/v1/accounting/fiscal-periods/deleted
{'POST'} /api/v1/accounting/fiscal-periods/{item_id}/restore
{'GET'} /api/v1/accounting/fiscal-periods/{item_id}/linked-documents
{'GET'} /api/v1/accounting/fiscal-periods/{item_id}
{'PUT'} /api/v1/accounting/fiscal-periods/{item_id}
{'PATCH'} /api/v1/accounting/fiscal-periods/{item_id}
{'DELETE'} /api/v1/accounting/fiscal-periods/{item_id}
{'POST'} /api/v1/accounting/fiscal-periods/bulk-delete
{'POST'} /api/v1/accounting/fiscal-periods/batch
{'GET'} /api/v1/accounting/grn-lines/metadata
{'GET'} /api/v1/accounting/grn-lines/
{'GET'} /api/v1/accounting/grn-lines
{'GET'} /api/v1/accounting/grn-lines/aggregate
{'GET'} /api/v1/accounting/grn-lines/export
{'POST'} /api/v1/accounting/grn-lines/import
{'POST'} /api/v1/accounting/grn-lines/
{'POST'} /api/v1/accounting/grn-lines
{'GET'} /api/v1/accounting/grn-lines/{item_id}/linked-documents
{'GET'} /api/v1/accounting/grn-lines/{item_id}
{'PUT'} /api/v1/accounting/grn-lines/{item_id}
{'PATCH'} /api/v1/accounting/grn-lines/{item_id}
{'DELETE'} /api/v1/accounting/grn-lines/{item_id}
{'POST'} /api/v1/accounting/grn-lines/bulk-delete
{'POST'} /api/v1/accounting/grn-lines/batch
{'GET'} /api/v1/accounting/grns/metadata
{'GET'} /api/v1/accounting/grns/
{'GET'} /api/v1/accounting/grns
```

Filtered route confirmation for audited custom routes:
```text
{'GET'} /api/v1/pot/sessions/{session_id}/items
{'POST'} /api/v1/pot/sessions/{session_id}/quick_invoice
{'GET'} /api/v1/report/erp/report/profit-loss
{'GET'} /api/v1/report/erp/report/balance-sheet
{'GET'} /api/v1/report/erp/report/trial-balance
{'GET'} /api/v1/stock/items/{item_id}/stock
```
