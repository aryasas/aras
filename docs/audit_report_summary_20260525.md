# Aras Audit Summary - 2026-05-25

Source reports:
- `docs/gemini_audit_report_20260525.md`
- `docs/gpt_audit_report_20260525.md`

## Executive Summary

Both audits agree that Aras is not production-ready yet. The main blockers are authorization and tenant isolation gaps in generic/dynamic endpoints, unsafe report execution paths, startup-time schema mutation, weak mobile/PWA deployment foundations, and missing regression tests around the generic framework behavior.

The highest-impact theme is simple: Aras has powerful generic architecture, but production safety must be enforced at the framework layer. Any gap in `RouterFactory`, metadata, report execution, scope handling, or generated UI affects every installed app.

## Consensus Blockers

### 1. Tenant and Org Isolation Is Not Trustworthy

- **Files**: `api/core/auth/service.py`, `api/core/logic/permissions.py`, `api/core/logic/router_factory.py`, `api/core/api/query.py`
- **Risk**: Users can influence `X-Org-ID` / scope headers, and several generic operations do not consistently enforce ownership checks.
- **Combined Fix**:
  - Validate requested org/scope IDs against the authenticated user's memberships before setting `request.state.scope`.
  - Apply scope checks to list, get, query, batch, bulk-delete, restore, linked-docs, custom actions, and app-specific endpoints.
  - Add regression tests proving a non-admin cannot read, update, delete, batch-update, query, or print another org's records.

### 2. Report Execution Is Unsafe

- **Files**: `api/apps/report/services/report_service.py`
- **Risk**: One audit flags arbitrary Python execution through `exec(report.script, ctx, ctx)`; the other flags unrestricted persisted SQL execution.
- **Combined Fix**:
  - Remove Python `exec()` report support.
  - Replace script reports with registered Python handler names or a constrained query/report DSL.
  - For SQL reports, enforce allowed tables/columns, read-only execution, row limits, statement timeouts, and org-scope injection.

### 3. Unauthenticated Metadata and App-Specific Endpoints Leak Data

- **Files**: `api/core/api/registry.py`, `api/apps/accounting/app.py`, `api/apps/accounting/routers/print_router.py`
- **Risk**: Metadata and accounting helper routes expose internal model structure and business data without proper auth/RBAC.
- **Combined Fix**:
  - Require auth/RBAC for `/metadata`, `/models`, `/schemas`, and `/views`.
  - Keep public metadata only for resources explicitly marked public.
  - Add `check_permissions()` and org-scope checks to accounting `open_invoices` and print endpoints.

### 4. Startup and Migration Strategy Is Not Production-Safe

- **Files**: `api/main.py`
- **Risk**: Schema creation and auto-migration run during import/startup, creating race conditions and deployment drift in multi-worker environments.
- **Combined Fix**:
  - Move schema mutation out of app import/startup for production.
  - Use Alembic migrations and run `alembic upgrade head` in CI/deploy.
  - Keep `manage.py sync` / auto-migrate as explicit development or admin operations only.

### 5. Sync SQLAlchemy Is Used Inside Async Routes

- **Files**: `api/core/lib/database.py`, `api/core/logic/router_factory.py`
- **Risk**: Sync `Session`/`psycopg2` work inside `async def` routes can block the FastAPI event loop under load.
- **Combined Fix**:
  - Short term: make DB-heavy routes synchronous `def` so FastAPI uses the threadpool.
  - Long term: migrate to `AsyncSession` with an async Postgres driver and audit all service calls for async compatibility.

## High-Priority Product Risks

### Security

- Fix auth rate limiter route mismatch: protect `/api/v1/auth/token`, not `/api/v1/auth/login`.
- Throttle forgot-password and reset-password endpoints.
- Stop printing password reset tokens except behind an explicit development-only guard.
- Sanitize CMS HTML before rendering `dangerouslySetInnerHTML` in `ui/src/views/WebPageView.tsx`.
- Move browser tokens out of `localStorage` or compensate with strong CSP, short-lived tokens, and refresh rotation.
- Add upload size/type allowlists and stream file writes.

### Data Integrity

- Fix `api/core/base/model.py` M2M bug: `bridge_table_name` is undefined in `save_m2m()`.
- Restrict automatic cascading deletes to explicitly owned child models.
- Normalize action permission names such as `"edit"` vs `UPDATE`.
- Make batch operations transactional and scoped, with per-operation validation.

### Performance

- Cache metadata generation and invalidate it on sync/layout changes.
- Optimize FK label and M2M resolution; avoid schema reflection through `autoload_with` on normal reads.
- Cap `per_page` to a production-safe value.
- Stream CSV import/export instead of reading entire files into memory.
- Debounce and cancel frontend list search requests.

### Mobile and PWA

- Add `ui/public/manifest.webmanifest`, service worker/offline fallback, `theme-color`, real app title, Apple mobile metadata, and safe-area handling.
- Increase mobile input/control font sizes and touch targets to avoid iOS zoom and accessibility failures.
- Configure Expo with production HTTPS API URL, bundle/package identifiers, scheme/deep links, splash, runtime version, and update channels.
- Treat mobile deployment as blocked until PWA/native configuration is complete.

## Testing Gaps To Close First

1. Cross-org isolation tests for CRUD, `/query`, `/batch`, `bulk-delete`, print endpoints, and report execution.
2. Report execution tests proving Python scripts cannot run and SQL reports are scoped/read-only/limited.
3. RouterFactory tests for child save, batch operations, M2M save, soft delete/restore, and permissions.
4. UIGenerator metadata tests for fields, choices, lookups, hidden fields, layout JSON, and public/private metadata behavior.
5. Frontend tests for `DynamicForm`, `ListView`, mobile card layout, search debounce, and generated schema mapping.
6. CI workflow for backend tests, frontend lint/build, mobile typecheck, and migration verification.

## Top 10 Priority Actions

1. **Blocker**: Validate `X-Org-ID` and all scope headers against user membership, then enforce scope across generic and app-specific endpoints.
2. **Blocker**: Remove Python `exec()` report execution and constrain SQL report execution.
3. **Blocker**: Add auth/RBAC to metadata/model/schema/view endpoints and accounting helper/print routes.
4. **Blocker**: Replace startup schema mutation with Alembic/deploy-time migrations.
5. **High**: Standardize FastAPI route sync/async behavior to stop event-loop blocking.
6. **High**: Fix rate limiting for `/auth/token`, forgot-password, and reset-password.
7. **High**: Fix `save_m2m()` and add framework regression tests.
8. **High**: Sanitize CMS HTML and harden token handling/CSP.
9. **High**: Add metadata caching and optimize FK/M2M resolution.
10. **Mobile Blocker**: Add PWA/native deployment foundations: manifest, service worker, safe areas, HTTPS API config, Expo identifiers, and deep links.

## Recommended Implementation Order

Phase 1 should be security and data isolation: scope validation, metadata auth, report execution removal, accounting route auth, and rate limiter fixes.

Phase 2 should stabilize the framework runtime: migration workflow, sync/async route strategy, M2M bug fix, cascade rules, and file/import/export limits.

Phase 3 should improve performance and mobile readiness: metadata cache, FK/M2M batching, frontend request cancellation, PWA manifest/service worker, mobile safe areas, and Expo production config.

Phase 4 should lock it down with tests and CI. The most important tests are cross-org isolation and RouterFactory regression tests because failures there affect every app built on Aras.
