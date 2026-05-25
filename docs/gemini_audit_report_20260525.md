# Aras Project Audit Report — 2026-05-25

## Executive Summary
Aras is a powerful metadata-driven framework, but several critical architectural and security gaps must be addressed before production deployment. The most significant risks are **unverified tenant isolation (X-Org-ID trust)** and **synchronous DB operations blocking the async event loop**, which will lead to security breaches and performance collapse under moderate load.

---

## 1. Critical Severity Findings

### [Security] Unverified Tenant Isolation (X-Org-ID Trust)
- **File**: `api/core/auth/service.py` (L68–75), `api/core/logic/permissions.py`
- **Platform**: `backend`
- **Issue**: The framework trusts the `X-Org-ID` header from the client without verifying if the authenticated user has access to that organization. A user can access any organization's data simply by guessing or knowing its ID.
- **Fix**: In `get_current_user` or `check_permissions`, verify the requested `org_id` against the user's allowed organizations (e.g., call `get_user_org_list(db, user)` and check if the requested ID is present).

### [Performance] Synchronous DB Sessions in Async Routes
- **File**: `api/core/lib/database.py` (L7–15), `api/core/logic/router_factory.py` (all CRUD routes)
- **Platform**: `backend`
- **Issue**: The backend uses synchronous `sqlalchemy.create_engine` and `SessionLocal` with a synchronous driver (`psycopg2-binary`), but all routes are declared as `async def`. This blocks the FastAPI event loop for every DB query, negating the benefits of async and causing the server to hang under load.
- **Fix**: Either change all generic routes to synchronous `def` (so FastAPI runs them in a thread pool) or migrate to `AsyncSession` with an async driver like `psycopg` (v3) or `asyncpg`.

### [Architecture] DB Migration/Sync on Module Import
- **File**: `api/main.py` (L30–33)
- **Platform**: `backend`
- **Issue**: `Aras.Base.metadata.create_all` and `Aras.logic.auto_migrate.run` are called during module initialization. This blocks startup and can cause race conditions or deployment failures in multi-worker environments (Gunicorn/Uvicorn).
- **Fix**: Move DB initialization and migrations into the `lifespan` context manager or a dedicated CLI command (`python manage.py migrate`).

### [Testing] SQLite Mandate Violation
- **File**: `tests/test_framework.py` (L20), `pytest.ini`
- **Platform**: `backend`
- **Issue**: Existing core tests use SQLite, explicitly violating the development mandate in `docs/aras.md` (L351) that forbids SQLite for tests to ensure compatibility with production Postgres/MySQL features.
- **Fix**: Update `conftest.py` to use a test Postgres database as per project standards.

---

## 2. High Severity Findings

### [Performance] Lack of Metadata Caching
- **File**: `api/core/logic/ui_generator.py` (L14), `api/core/logic/router_factory.py` (L215)
- **Platform**: `backend`
- **Issue**: The `/metadata` endpoint regenerates the entire resource schema (FK discovery, M2M resolution, labels) on every request. This is computationally expensive.
- **Fix**: Implement an in-memory or Redis-based cache for `UIGenerator.generate_metadata`. Invalidate cache only when `manage.py sync` is run.

### [Bugs] Inefficient M2M & FK Label Resolution
- **File**: `api/core/base/model.py` (L318), `api/core/base/model.py` (L413)
- **Platform**: `backend`
- **Issue**: `resolve_m2m` uses `autoload_with=db.connection()`, which queries the DB schema on every fetch. `resolve_labels` performs separate queries for each batch/column.
- **Fix**: Register bridge tables in `Base.metadata` at startup to avoid `autoload`. Optimize `resolve_labels` to group lookups by target table.

### [Security] Path Mismatch in Auth Rate Limiting
- **File**: `api/core/lib/rate_limiter.py` (L20)
- **Platform**: `backend`
- **Issue**: The rate limiter attempts to protect `/api/v1/auth/login`, but the actual login endpoint is `/api/v1/auth/token`. Auth is currently unprotected (falling back to default 200/60).
- **Fix**: Update `_ROUTE_LIMITS` in `RateLimiterMiddleware` to include `/api/v1/auth/token`.

### [Bugs] Aggressive Cascading Deletes
- **File**: `api/core/base/model.py` (L514–535)
- **Platform**: `backend`
- **Issue**: `_cascade_linked_docs` automatically deletes ALL records with non-nullable FKs to the parent. This can lead to catastrophic data loss for shared resources that are incorrectly marked non-nullable.
- **Fix**: Restrict auto-cascade to models explicitly marked for ownership or use the `__linked_docs__` escape hatch with `cascade=True`.

---

## 3. Medium Severity Findings

### [UX] iOS Auto-zoom Prevention
- **File**: `ui/src/index.css` (L417)
- **Platform**: `mobile-web`
- **Issue**: Mobile input font-size is set to `14px`. iOS triggers an automatic zoom-in on focus if font-size is less than `16px`, breaking the mobile UX.
- **Fix**: Set `font-size: 16px` for all `input`, `select`, and `textarea` in the mobile media query.

### [Performance] Redundant Metadata/Menu Fetches
- **File**: `ui/src/layouts/MainLayout.tsx` (L55), `ui/src/views/SmartDispatcher.tsx` (L45)
- **Platform**: `web` / `mobile-web`
- **Issue**: The sidebar and app-menu are fetched on every mount of the layout/dispatcher, causing flickering and unnecessary load.
- **Fix**: Cache sidebar/menu data in `uiStore` or use a caching layer in `api.ts` (e.g., React Query).

### [Code Quality] Duplicated Scoping Logic
- **File**: `api/core/logic/router_factory.py` (L23–31) vs `api/core/logic/scope.py`
- **Platform**: `backend`
- **Issue**: `_scope_fields` and scope extraction logic are duplicated.
- **Fix**: Consolidate all scope extraction and validation into `api/core/logic/scope.py`.

---

## 4. Multi-Platform UI/UX Audit

### 4a. Web (Desktop)
- **Accessibility**: Keyboard focus rings are missing or inconsistent on custom components like `Combobox`.
- **Consistency**: Primary action button (Save/Add) is on the left (`.arc-actionbar`), which is consistent but unconventional for Windows/Linux users (though okay for Mac-centric design).

### 4b. Mobile Web
- **Touch Targets**: Mobile buttons are 42px high; 44px is the industry standard for accessibility.
- **Responsiveness**: Cards in `ListView` on mobile look good, but the lack of a "back" button in the `Header` makes navigation difficult after clicking a record.

### 4c. Mobile App (Standalone)
- **Safe Area**: No usage of `padding-safe-area-inset` found in `index.css`. The header may be cut off by the notch on iOS.
- **PWA**: `manifest.json` is not present in `ui/` or `ui/public/`.

---

## 5. Production Readiness Gaps
- **[Critical] Health Check**: No public `/health` or `/api/v1/health` endpoint for load balancer health probes.
- **[High] Structured Logging**: Logging is JSON-formatted but lacks `request_id` or `correlation_id` to trace a single request through the logs.
- **[High] Error Response Consistency**: `generic_exception_handler` returns `500` but doesn't follow the exact same envelope as `ArasException` in all cases (nested `error` field vs flat).
- **[Medium] Cache Busting**: Static assets in `index.html` are not versioned/cache-busted.

---

## 6. Testing Coverage Gaps
- **[Critical]** `RouterFactory`: 0% unit tests for the complex `batch_operations` and `_save_children` logic.
- **[Critical]** `UIGenerator`: 0% unit tests for metadata generation accuracy.
- **[High]** Frontend: 0% unit or integration tests for `DynamicForm` and `ListView`.
- **[High]** Auth: `test_auth_security.py` exists but does not test the `X-Org-ID` bypass reported here.

---

## Priority Action List (Top 10)

1. **[BLOCKER] Fix X-Org-ID verification** in `api/core/auth/service.py` to prevent cross-tenant data access.
2. **[STABILITY] Standardize Route Sync/Async**: Change CRUD routes to `def` (sync) to stop blocking the event loop.
3. **[STABILITY] Move DB initialization** out of module import in `api/main.py`.
4. **[SECURITY] Correct Rate Limiter path** for auth: change `/auth/login` → `/auth/token`.
5. **[PERFORMANCE] Cache Metadata** in `UIGenerator` to reduce DB load and improve latency.
6. **[PRODUCTION] Add `/api/v1/health`** endpoint that pings the DB.
7. **[MOBILE] Increase mobile font-size to 16px** to prevent iOS auto-zoom.
8. **[REUSABILITY] Refactor bridge table resolution** to avoid `autoload_with` in `resolve_m2m`.
9. **[TESTING] Migrate test suite to Postgres** and remove SQLite dependency.
10. **[MOBILE] Add Safe Area padding** to `MainLayout` and `Header` for notch compatibility.

---
*Report generated by Gemini CLI — Senior Architect Audit*
