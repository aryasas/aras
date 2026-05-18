### AGENT REPORT
- files_written: api/apps/erp/hr/app.py, api/apps/erp/asset/app.py, api/apps/erp/party/app.py, api/apps/erp/pot/app.py, api/apps/erp/crm/app.py, api/apps/erp/stock/app.py, api/apps/erp/report/app.py, api/apps/erp/accounting/app.py, api/apps/erp/config/app.py, api/core/registry/user_role.py, api/core/logic/permissions.py, api/core/auth/routes.py, api/apps/erp/config/erp_rbac.py
- features_added: Implemented ERP org-scoped RBAC with new model and 5 endpoints.
- fixes_applied: Standardized ERP module registration (app_name, app_type), removed UserRole.company_id and integrated ERP org list in auth routes.
- framework_changes: RBAC permission checking adjusted to remove company_id parameter, UserRole model simplified.
- issues: none