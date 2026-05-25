# Aras Project Audit - 2026-05-25

Scope: active `api/`, `ui/`, `mobile/`, `tests/`, and deploy/install artifacts. Archived `aras-old/` files were excluded from findings unless the active app references them.

## Critical

- **File**: `api/apps/report/services/report_service.py` (line 149)
  **Severity**: `critical`
  **Platform**: `backend`
  **Issue**: Report definitions with `report_type == "script"` execute arbitrary Python via `exec(report.script, ctx, ctx)`.
  **Fix**: Remove Python script execution from persisted reports; replace with a whitelist of registered report handler functions or a constrained SQL/query DSL, and migrate existing script reports to handlers.

- **File**: `api/core/api/registry.py` (lines 12-80)
  **Severity**: `critical`
  **Platform**: `backend`
  **Issue**: `/api/v1/metadata/{resource}`, `/api/v1/models`, `/api/v1/schemas`, and `/api/v1/views` expose model names, fields, registry internals, and UI metadata without authentication or RBAC.
  **Fix**: Add `Depends(check_permissions(..., "READ"))` to metadata resolution and `Depends(require_admin)` to `/models`, `/schemas`, and `/views`; keep public metadata only for models explicitly marked public.

- **File**: `api/apps/accounting/app.py` (lines 13-16) and `api/apps/accounting/routers/print_router.py` (lines 17-24)
  **Severity**: `critical`
  **Platform**: `backend`
  **Issue**: Accounting extra routers are mounted with no auth dependency, exposing open invoices and printable invoices by numeric ID.
  **Fix**: Add `Depends(check_permissions("erp_accounting_payments", "READ"))` to `open_invoices` and resource-specific READ checks plus org-scope checks to the print endpoint before returning document data.

- **File**: `ui/src/views/WebPageView.tsx` (lines 63-65) and `api/apps/web/routers.py` (lines 22-30)
  **Severity**: `critical`
  **Platform**: `web`
  **Issue**: Public CMS page content from the database is rendered with `dangerouslySetInnerHTML` without sanitization.
  **Fix**: Sanitize `page.content` server-side with an allowlist HTML sanitizer before storing or returning it, and sanitize again client-side with a vetted sanitizer if rich HTML must remain editable.

## High

- **File**: `api/core/base/model.py` (lines 600-609)
  **Severity**: `high`
  **Platform**: `backend`
  **Issue**: `save_m2m()` assigns `bridge_table = ...` but calls `Table(bridge_table_name, ...)`, so every M2M save raises `NameError`.
  **Fix**: Replace `bridge_table_name` with `bridge_table` and add a unit test that creates, updates, and clears a declared `__m2m__` field.

- **File**: `api/core/logic/router_factory.py` (lines 630-648, 655-747)
  **Severity**: `high`
  **Platform**: `backend`
  **Issue**: `bulk_delete()` and list-shaped `/batch` operations never call `_check_scope_ownership`, allowing a scoped user with resource permission to delete or update records outside the selected `X-Org-ID`.
  **Fix**: Require `Request` in these handlers and call `_check_scope_ownership(model_class, request, item)` before each update/delete.

- **File**: `api/core/api/query.py` (lines 20-48)
  **Severity**: `high`
  **Platform**: `backend`
  **Issue**: Generic query API enforces RBAC but does not apply `__scoped_by__` filters from `X-Org-ID` or `X-Scope-*`, so cross-org data can be returned.
  **Fix**: Accept `Request`, build a `ScopeContext`, append scope filters exactly as `RouterFactory.list_items()` does, and add an org-isolation regression test.

- **File**: `api/core/auth/service.py` (lines 65-72) and `api/core/logic/permissions.py` (lines 22-24)
  **Severity**: `high`
  **Platform**: `backend`
  **Issue**: `X-Org-ID` and `X-Scope-*` headers are trusted directly from the client; membership in the selected organization is not verified.
  **Fix**: Validate scope values against the authenticated user's allowed organizations/scopes before writing `request.state.scope`; reject unauthorized scope IDs with 403.

- **File**: `api/core/lib/rate_limiter.py` (lines 20-24) and `api/core/auth/routes.py` (lines 33-50, 92-132)
  **Severity**: `high`
  **Platform**: `backend`
  **Issue**: Rate-limit route keys target `/api/v1/auth/login` and `/api/v1/auth/register`, but the actual login route is `/api/v1/auth/token`, and forgot/reset password routes are not throttled.
  **Fix**: Change the auth limit key to `/api/v1/auth/token`, add limits for `/api/v1/auth/forgot-password` and `/api/v1/auth/reset-password`, and test 429 behavior.

- **File**: `api/core/auth/routes.py` (lines 102-108)
  **Severity**: `high`
  **Platform**: `backend`
  **Issue**: Password reset tokens are printed to stdout.
  **Fix**: Remove token printing and send reset links through a mail service; in development, guard any token display behind `settings.DEBUG`.

- **File**: `api/apps/report/services/report_service.py` (lines 60-68)
  **Severity**: `high`
  **Platform**: `backend`
  **Issue**: Persisted report SQL is executed if it starts with `SELECT`; there is no table/column whitelist, timeout, row limit, or read-only transaction enforcement.
  **Fix**: Execute reports through a whitelisted query builder or validate SQL AST against allowed tables and enforce statement timeout plus `LIMIT`.

- **File**: `api/core/tenant/provisioner.py` (lines 48-50, 121-135)
  **Severity**: `high`
  **Platform**: `backend`
  **Issue**: Tenant database names are interpolated into `CREATE DATABASE` and `ALTER DATABASE` identifiers from request-controlled input.
  **Fix**: Validate `tenant_id` and `db_name` against `^[a-z][a-z0-9_]{2,62}$`; reject invalid names before constructing quoted identifiers.

- **File**: `api/core/lib/storage.py` (lines 13-24) and `api/core/api/files.py` (lines 11-20)
  **Severity**: `high`
  **Platform**: `backend`
  **Issue**: Uploads read the whole file into memory, preserve any extension, do not cap size, and do not enforce MIME/extension allowlists.
  **Fix**: Stream uploads in chunks with a configured max size; validate allowed MIME types/extensions per field and reject oversized files before writing.

- **File**: `mobile/src/lib/api.ts` (line 4)
  **Severity**: `high`
  **Platform**: `mobile-app`
  **Issue**: Native app default API base URL is `http://localhost:8000/api/v1`, which fails on physical iOS/Android devices and is not TLS.
  **Fix**: Require `EXPO_PUBLIC_API_BASE_URL` for mobile builds, use an HTTPS production URL, and fail app startup with a visible configuration error when missing.

## Medium

- **File**: `api/main.py` (lines 42-46)
  **Severity**: `medium`
  **Platform**: `backend`
  **Issue**: Production startup runs `metadata.create_all()` and custom `auto_migrate.run()` instead of Alembic-managed migrations.
  **Fix**: Move schema changes to Alembic, run `alembic upgrade head` in deploy/CI, and disable startup DDL outside development.

- **File**: `api/main.py` (lines 50-57)
  **Severity**: `medium`
  **Platform**: `backend`
  **Issue**: Lifespan opens `db = next(Aras.get_db())` but never closes the generator/session.
  **Fix**: Use `with SessionLocal() as db:` or explicitly close the yielded session in a `finally` block.

- **File**: `api/core/logic/router_factory.py` (lines 291-336)
  **Severity**: `medium`
  **Platform**: `backend`
  **Issue**: `per_page` allows up to `999999`, enabling very large DB reads and JSON responses.
  **Fix**: Cap `per_page` at a production-safe value such as 100 or 250 and expose CSV export/background jobs for larger datasets.

- **File**: `api/core/base/model.py` (lines 365-367, 378-459)
  **Severity**: `medium`
  **Platform**: `backend`
  **Issue**: Each paginated list resolves FK labels by scanning all columns and issuing separate queries per FK/display column.
  **Fix**: Precompute FK label metadata per model and batch related label lookups in one helper; for common relations use `selectinload` or explicit joins.

- **File**: `api/core/logic/router_factory.py` (lines 425-445)
  **Severity**: `medium`
  **Platform**: `backend`
  **Issue**: CSV import reads the entire uploaded file and parsed rows into memory before enqueueing.
  **Fix**: Store the upload as a temporary file/object and pass a task reference; parse rows inside the background task with row and size limits.

- **File**: `api/core/logic/router_factory.py` (lines 247-811)
  **Severity**: `medium`
  **Platform**: `backend`
  **Issue**: `create_router()` contains metadata, CRUD, import/export, soft-delete, batch, child persistence, and model action handlers in one large factory.
  **Fix**: Extract child sync, CSV import/export, batch operations, and schema generation into service modules with focused tests.

- **File**: `api/core/base/model.py` (lines 236-293) and `api/core/lib/query_builder.py` (lines 15-47)
  **Severity**: `medium`
  **Platform**: `backend`
  **Issue**: Two filter implementations support different operator names (`=` vs `==`) and different operator sets.
  **Fix**: Delete `QueryBuilder` filtering logic or delegate it to `Model.apply_filters()` through one shared filter parser/operator map.

- **File**: `api/core/api/websocket.py` (line 40)
  **Severity**: `medium`
  **Platform**: `backend`
  **Issue**: WebSocket auth was not confirmed in the mounted `/api/v1/ws` route during static review; if token validation is optional or only query-based, browser clients can connect without normal auth middleware.
  **Fix**: Require JWT validation during `websocket.accept()` setup and close with policy violation when missing/invalid.

- **File**: `ui/src/lib/api.ts` (lines 47-50) and `ui/src/store/authStore.ts` (lines 36-44)
  **Severity**: `medium`
  **Platform**: `web`
  **Issue**: JWT access tokens are stored in `localStorage`, increasing exposure from any XSS in the dynamic UI/CMS.
  **Fix**: Move auth to secure HttpOnly SameSite cookies or use short-lived access tokens with refresh rotation and CSP.

- **File**: `ui/src/aras-core/components/DynamicForm.tsx` (lines 99-120)
  **Severity**: `medium`
  **Platform**: `web`
  **Issue**: Metadata and record fetch effects have no cancellation guard; stale responses can overwrite state after rapid route/resource changes.
  **Fix**: Use `AbortController` or an `isCurrent` flag for both requests and ignore late responses in cleanup.

- **File**: `ui/src/aras-core/components/ListView.tsx` (lines 107-150, 191-193)
  **Severity**: `medium`
  **Platform**: `web`
  **Issue**: Search fires a list request on every keystroke without debounce or request cancellation.
  **Fix**: Debounce search input and abort in-flight list requests before starting the next one.

- **File**: `ui/src/aras-core/components/ListView.tsx` (lines 122-139)
  **Severity**: `medium`
  **Platform**: `web`
  **Issue**: Client-side `activeOrgId` is appended as a normal filter, duplicating and potentially diverging from backend scope enforcement.
  **Fix**: Remove client-injected `org_id` filters and rely on validated backend scope from `X-Org-ID`.

- **File**: `ui/src/aras-core/components/ListView.tsx` (lines 363-375)
  **Severity**: `medium`
  **Platform**: `web`
  **Issue**: Grouping is done only on the current page of data, so group counts and sections are misleading for paginated datasets.
  **Fix**: Either label grouping as page-local or add server-side grouped query support with total counts per group.

- **File**: `ui/src/aras-core/components/ListView.tsx` (lines 346-347, 475-477)
  **Severity**: `medium`
  **Platform**: `mobile-web`
  **Issue**: Desktop table calculates a large min width, while mobile renders separate cards; intermediate widths around `md` can still horizontally scroll for wide schemas.
  **Fix**: Add a tablet breakpoint strategy: cap visible default columns, keep horizontal scroll explicit at `sm/md`, and persist per-resource responsive column defaults.

- **File**: `ui/src/aras-core/components/ListViewActionBar.tsx` (lines 119-128, 217-229, 310-320)
  **Severity**: `medium`
  **Platform**: `mobile-web`
  **Issue**: Core toolbar controls use 28px high touch targets (`h-7`, `w-7`), below the 44x44 mobile target.
  **Fix**: Use `min-h-[44px] min-w-[44px]` for icon buttons and compact visual padding inside the button, at least below `md`.

- **File**: `ui/src/aras-core/components/DynamicForm.tsx` (lines 234-266, 319-329)
  **Severity**: `medium`
  **Platform**: `mobile-web`
  **Issue**: Generated form action buttons also use 28-32px heights and action labels like `Approve` for a generic save path.
  **Fix**: Increase mobile button targets to 44px and derive submit label from operation/workflow metadata instead of hardcoding `Approve`.

- **File**: `ui/index.html` (lines 5-7)
  **Severity**: `medium`
  **Platform**: `mobile-app`
  **Issue**: The web app has no PWA manifest link, app theme color, Apple mobile web app metadata, or production title.
  **Fix**: Add `public/manifest.webmanifest`, link it in `index.html`, set `theme-color`, Apple status bar metadata, and a real app title.

- **File**: `ui/public` (directory)
  **Severity**: `medium`
  **Platform**: `mobile-app`
  **Issue**: No service worker or offline fallback exists for standalone PWA use.
  **Fix**: Add a Vite PWA/service worker setup with app-shell caching, offline fallback, and API/network failure states.

- **File**: `mobile/app.json` (lines 9-25)
  **Severity**: `medium`
  **Platform**: `mobile-app`
  **Issue**: Expo native config lacks bundle identifiers/package names, scheme/deep-link config, splash config, runtime version, and update/channel policy.
  **Fix**: Add `ios.bundleIdentifier`, `android.package`, `scheme`, splash settings, runtime version, and documented EAS update channels.

## Low

- **File**: `api/core/lib/query_builder.py` (line 7)
  **Severity**: `low`
  **Platform**: `backend`
  **Issue**: `or_` is imported but unused.
  **Fix**: Remove the unused import when consolidating filter logic.

- **File**: `api/core/logic/router_factory.py` (lines 9-11)
  **Severity**: `low`
  **Platform**: `backend`
  **Issue**: `Any` and `Optional` are imported twice from `typing`.
  **Fix**: Collapse to a single `from typing import Any, List, Optional, Type, Union, get_args, get_origin`.

- **File**: `api/apps/web/models.py` (lines 20-30, 52-55)
  **Severity**: `low`
  **Platform**: `backend`
  **Issue**: Model actions use permission `"edit"` while generated CRUD/RBAC conventions use uppercase actions such as `UPDATE`.
  **Fix**: Change action permissions to `UPDATE` and update seed permissions if custom action names are intentionally supported.

- **File**: `ui/src/App.tsx` (lines 103-113)
  **Severity**: `low`
  **Platform**: `web`
  **Issue**: Overriding `window.confirm` always returns `false`, breaking any legacy code that expects synchronous confirmation.
  **Fix**: Remove the global override or expose an async app confirm helper and migrate callers explicitly.

- **File**: `ui/src/aras-core/components/ListView.tsx` (lines 681-704) and `ui/src/aras-core/components/DynamicForm.tsx` (lines 52-64)
  **Severity**: `low`
  **Platform**: `web`
  **Issue**: Status glyph/color maps are duplicated in list and form components.
  **Fix**: Extract `getStatusMeta()` and `StatusGlyph/StatusBadge` into a shared UI utility/component.

- **File**: `ui/src/aras-core/components/ListViewActionBar.tsx` (lines 84, 154-157) and `ui/src/aras-core/components/ListView.tsx` (line 405)
  **Severity**: `low`
  **Platform**: `web`
  **Issue**: The "save filter" action is rendered when filters exist but is wired to an empty callback.
  **Fix**: Implement saved-filter creation or hide the button until the callback is functional.

- **File**: `ui/public` (directory)
  **Severity**: `low`
  **Platform**: `web`
  **Issue**: `robots.txt` and `sitemap.xml` are absent for the public CMS/landing routes.
  **Fix**: Add static `robots.txt` and sitemap generation for published web pages if these routes are public-facing.

- **File**: `.github/workflows` (directory missing) and repository root
  **Severity**: `low`
  **Platform**: `all`
  **Issue**: No CI workflow was found for backend tests, frontend lint/build, mobile typecheck, or migrations.
  **Fix**: Add CI that runs backend tests, type/lint/build for `ui`, mobile typecheck, and migration verification.

## Testing Coverage Gaps

- **File**: `tests/` and `api/core/logic/router_factory.py` (lines 630-747)
  **Severity**: `high`
  **Platform**: `backend`
  **Issue**: No visible regression test covers org-scope enforcement for `bulk-delete`, `/batch`, or generic `/query`.
  **Fix**: Add tests using two orgs and a non-admin user, asserting scoped users cannot read/update/delete the other org's records.

- **File**: `tests/` and `ui/src/aras-core/components/DynamicForm.tsx` (lines 201-221, 311-313)
  **Severity**: `medium`
  **Platform**: `web`
  **Issue**: Auto UI schema-to-layout mapping has no component test visible for layouts, hidden fields, lookup fields, and mobile reflow.
  **Fix**: Add React Testing Library tests for generated form layout and Playwright visual tests at desktop/tablet/mobile widths.

- **File**: `tests/` and `ui/src/aras-core/components/ListView.tsx` (lines 107-150, 468-581)
  **Severity**: `medium`
  **Platform**: `web`
  **Issue**: Core list behavior lacks visible E2E coverage for search/filter/sort/pagination/import/export/mobile cards.
  **Fix**: Add Playwright flows for CRUD list interactions with mocked or seeded metadata.

## Priority Action List

1. Remove `exec()` report execution and migrate script reports to registered handlers. **Blocks production.**
2. Add auth/RBAC to registry metadata/model/schema/view endpoints. **Blocks production.**
3. Add auth and org-scope checks to accounting open-invoice and print endpoints. **Blocks production.**
4. Validate client-supplied org/scope headers against user membership and apply scope to `/query`, `/batch`, and `bulk-delete`. **Blocks production.**
5. Sanitize CMS HTML before rendering. **Blocks production and mobile web.**
6. Fix `save_m2m()` `bridge_table_name` bug and add M2M regression tests.
7. Replace startup DDL/auto-migrate in production with Alembic migration workflow and CI verification.
8. Correct rate-limit route keys and throttle forgot/reset password endpoints.
9. Add upload size/type limits and streaming upload/import handling.
10. Add PWA/native deployment basics: manifest, service worker/offline fallback, HTTPS API config, Expo identifiers/deep links. **Blocks mobile deployment.**
