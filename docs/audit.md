# Aras Project Audit — 2026-06-13

## Summary
- Total issues found: 48
- Critical (security/compliance): 4
- High (broken/missing features): 13
- Medium (incomplete/UX): 18
- Low (cleanup/polish): 13

## 1. Security & Compliance Issues

### [CRITICAL] Rate Limiting missing on Auth routes
- File: `api/core/auth/routes.py` line 44, 69, 147, 163, 193
- Issue: Compliance mandate requires 5/min rate limit on login, register, forgot-password, and reset-password. While `RateLimiterMiddleware` exists in `main.py`, it is not effectively protecting these routes because it depends on `request.state.user` which is not set by `get_current_user` in time for the middleware check on unauthenticated routes.
- Fix: Add explicit rate limiting dependencies to auth routes or ensure `RateLimiterMiddleware` correctly identifies routes based on IP even when `request.state.user` is missing.

### [CRITICAL] Read-Only SQL Runner Data Leakage
- File: `api/apps/dev/db_router.py` line 14
- Issue: The `run_sql_query` endpoint allows administrators to run arbitrary SELECT queries. It provides direct access to `core_users` table including `password` hashes, `saas_license_token`, and other PII/secrets, bypassing all framework-level PII redaction and audit logging.
- Fix: Implement column-level allowlists for the SQL runner or require a "super-admin" role.

### [CRITICAL] Insecure Token Storage Fallback (Mobile)
- File: `mobile/src/lib/storage.ts` line 20
- Issue: If `SecureStore.setItemAsync` fails, it silently falls back to an in-memory `Map`. On some Android devices with full storage or configuration issues, tokens could be lost on app restart, or worse, if a developer mistakenly uses a non-secure key for tokens, they might be logged or exposed.
- Fix: Ensure `aras_token` ALWAYS uses `SecureStore` and throws a hard error if security cannot be guaranteed.

### [CRITICAL] CSP Policy Weakness (Backend/Web)
- File: `api/core/api/middleware/security_headers.py` line 48
- Issue: Uses `style-src 'unsafe-inline'` due to Tailwind utility class requirements. This allows an attacker who can inject HTML to also inject arbitrary styles (e.g. for phishing overlays).
- Fix: Use a hash-based or nonce-based style-src if possible, or at least use `style-src-elem` more strictly.

## 2. Backend Issues

### [HIGH] Arbitrary Python Code Execution in Reports
- File: `api/core/report/services/report_service.py` line 88
- Issue: `ReportService._generate_script_report` uses `exec()` to run Python scripts defined in the database. Allows any admin to execute arbitrary code on the server.
- Fix: Replace `exec()` with a sandboxed environment or predefined logic keys.

### [HIGH] Inconsistent PII Redaction in Audit Logs
- File: `api/core/lib/audit.py` line 11 vs `api/core/manager/audit_manager.py` line 67
- Issue: `AuditManager` redacts PII, but `AuditService.record` (manual logging) saves the `diff` dictionary directly without redaction.
- Fix: Centralize PII redaction logic and apply to all audit paths.

### [HIGH] Incomplete Workflow Implementation
- File: `api/apps/ticket/models.py`, `api/apps/crm/models.py`
- Issue: Models marked with `__features__ = ["workflow"]` but no `WorkflowTemplate` or `WorkflowTransition` records are seeded.
- Fix: Seed default workflows for all apps using the `workflow` feature.

### [HIGH] Missing PII Tags in HR and Party Apps
- File: `api/apps/hr/models.py`, `api/apps/party/models.py`
- Issue: Several sensitive fields lack `pii=True`: `Employee.employee_code`, `Party.mobile`, `Party.address`.
- Fix: Audit all models and apply `pii=True` consistently.

### [MEDIUM] Soft-Delete Bypass in Child Relation Sync
- File: `api/core/logic/router_factory/helpers.py` line 121
- Issue: Uses `db.delete()` which performs a hard DELETE. Bypasses `SoftModel` logic.
- Fix: Use `item.delete_self(db)` to respect delete strategy.

### [MEDIUM] N+1 Query in Payment Allocation Serialization
- File: `api/apps/accounting/models.py` line 346
- Issue: `PaymentAllocation.invoice_number` is a computed field performing a DB query per row.
- Fix: Use `joinedload` or `resolve_labels` logic.

### [MEDIUM] Raw SQL Usage in Model Insights and POS
- File: `api/core/logic/router_factory/crud.py` line 231, `api/apps/pot/models.py` line 30
- Issue: Uses raw SQL strings or `text()` blocks, violating ORM-only mandate.
- Fix: Refactor to SQLAlchemy core `select()`/`func` expressions.

## 3. Frontend Web Issues

### [HIGH] Missing Field Types in DynamicForm
- File: `ui/src/aras-core/components/DynamicForm.tsx`
- Issue: `handleSubmit` and `validateForm` explicitly skip or lack implementation for `child_table`, `file`, and `image` field types. Users cannot upload assets or manage line-items in the primary form view.
- Fix: Implement file upload handling in `handleSubmit` and wire `childData` changes into the main save payload.

### [HIGH] Hardcoded Auth Token Fallback
- File: `ui/src/lib/api.ts` line 48
- Issue: `getAuthToken` still looks in `localStorage` for `aras_token`. While it migrates to `sessionStorage`, the initial presence in `localStorage` is a vulnerability on shared machines.
- Fix: Deprecate `localStorage` for tokens entirely and rely on httpOnly cookies if supported by backend.

### [MEDIUM] Hardcoded Primary Action Label
- File: `ui/src/aras-core/components/DynamicForm.tsx` line 515
- Issue: Primary button label is hardcoded to `{currentId ? 'Approve' : 'Save'}`. Using "Approve" for every existing record edit is confusing UX if the record is not in a "submitted" or "pending" workflow state.
- Fix: Derive button label from workflow metadata or use a generic "Save Changes".

### [MEDIUM] Generic Error Handling in Login
- File: `ui/src/views/Login.tsx` line 34
- Issue: Does not specifically handle 429 (Rate Limit) errors. It just displays the raw backend error string, which may not be user-friendly or provide a countdown.
- Fix: Add 429-specific state to show a lockout timer.

### [LOW] Non-functional UI Stubs
- File: `ui/src/aras-core/components/DynamicForm.tsx` line 484
- Issue: Share, Copy Link, and More buttons are rendered but have no implementation.
- Fix: Hide these buttons or implement a basic "Copy to Clipboard" for the URL.

## 4. Mobile Issues

### [HIGH] Missing Token Refresh Logic
- File: `mobile/src/lib/api.ts` line 84, `mobile/src/store/useAuthStore.ts`
- Issue: Mobile app logs out immediately on 401. It does not attempt to use a refresh token. With a 15-minute access token expiry, mobile users are logged out every 15 minutes.
- Fix: Implement 401 interceptor that calls `/auth/refresh` before giving up.

### [HIGH] Manual SecureStore access in AuthStore
- File: `mobile/src/store/useAuthStore.ts` line 56
- Issue: Bypasses the `lib/auth.ts` and `lib/storage.ts` abstractions to call `SecureStore.getItemAsync` directly. This breaks the platform-neutral storage logic and makes it harder to audit token usage.
- Fix: Use `getToken()` from `lib/auth.ts`.

### [MEDIUM] Missing Field Types in ResourceForm
- File: `mobile/src/screens/ResourceFormScreen.tsx` line 224
- Issue: Does not handle `file`, `image`, or `child_table` UI types. Complex documents cannot be edited on mobile.
- Fix: Implement `ImagePicker` for `image` type and a sub-screen for `child_table` editing.

### [MEDIUM] Naive Date Input
- File: `mobile/src/screens/ResourceFormScreen.tsx` line 290
- Issue: `date` fields use a plain `TextInput` with a placeholder `YYYY-MM-DD`. This is error-prone on mobile.
- Fix: Use `DateTimePicker` from `@react-native-community/datetimepicker`.

## 5. Missing Features (not bugs)
- [ ] Feature: Push Notifications (FCM/APNs) — Absent from mobile infrastructure.
- [ ] Feature: Biometric Authentication (FaceID/Fingerprint) — Absent from LoginScreen.
- [ ] Feature: Offline Queue — Mobile lacks a way to save records when offline and sync later.
- [ ] Feature: Camera/QR Scan — POS and Stock apps on mobile lack barcode scanning capabilities.
- [ ] Feature: Document Printing — No `expo-print` integration for POS receipts or Invoices.

## 6. Architecture / Code Quality
- File: `api/core/base/orm.py` line 59 — Naive `date.today()` used in defaults. Should be UTC.
- File: `api/apps/pot/services/pot.py` — Empty class stub `PotService`.
- File: `api/core/manager/naming_manager.py` vs `api/core/lib/numbering.py` — Duplicate document numbering logic.
- File: `mobile/src/lib/api.ts` — Hardcoded 15s timeout might be too short for slow cellular networks.

## 7. Dead Code / Stale Files
- File: `api/apps/dev/cause-error` — Temporary test endpoint left in codebase.
- File: `mobile/src/lib/apiBaseUrl.ts` — Duplicates some logic found in `lib/storage.ts` regarding workspace URL persistence.
