# Handoff Spec

> Written by: Codex GPT-5.5
> Date: 2026-05-25
> Feature: Production hardening from combined audit summary

---

## Context
Use `docs/audit_report_summary_20260525.md` as the source of truth. The goal of this run is to start fixing the highest-impact production blockers found by both audit reports, with backend focused on security/data isolation/report execution and frontend focused on mobile/PWA/security UX readiness.

This is an implementation handoff. Agents should make code changes, run focused verification, and report exact files changed. Keep scope tight: do not attempt unrelated rewrites.

---

## Backend Tasks

### Phase 1 — Security, Tenant Isolation, Reports

- UPDATE `api/core/auth/service.py` and `api/core/logic/permissions.py` — validate `X-Org-ID` and `X-Scope-*` values against the authenticated user's allowed organizations/scopes before storing them in `request.state.scope`. Reject unauthorized scope IDs with 403.
- UPDATE `api/core/logic/router_factory.py` — enforce scope ownership consistently for `bulk-delete`, list-shaped `/batch` updates/deletes, restore, linked-docs, and model action endpoints. Call the existing ownership helper before mutating or returning scoped records.
- UPDATE `api/core/api/query.py` — apply the same scope filters used by generic list endpoints so `/api/v1/{resource}/query` cannot return cross-org data.
- UPDATE `api/apps/report/services/report_service.py` — remove Python `exec()` report execution. Replace script execution with a blocked/generic error response or a registered-handler lookup if one already exists locally. Keep SQL/query reports functional.
- UPDATE `api/apps/report/services/report_service.py` — constrain SQL report execution: use `report.script`, enforce read-only SELECT-only behavior, apply org scope where possible, add a row limit or require explicit `LIMIT`, log internal errors with `logger.exception`, and return generic user-facing errors.
- UPDATE `api/core/api/registry.py` — require auth/RBAC for `/metadata/{resource_name:path}` and require admin for `/models`, `/schemas`, and `/views`. Keep only explicitly public resources publicly readable.
- UPDATE `api/apps/accounting/app.py` and `api/apps/accounting/routers/print_router.py` — add auth/RBAC and org-scope checks to `open_invoices` and printable accounting document endpoints.
- UPDATE `api/core/lib/rate_limiter.py` — protect the real login path `/api/v1/auth/token`; add stricter limits for `/api/v1/auth/forgot-password` and `/api/v1/auth/reset-password`.
- UPDATE `api/core/auth/routes.py` — remove password reset token printing unless explicitly guarded by `settings.DEBUG`.

### Phase 2 — Runtime/Data Integrity

- UPDATE `api/core/base/model.py` — fix `save_m2m()` undefined `bridge_table_name`; use the configured `bridge_table` value and add/adjust tests for M2M create/update/clear.
- UPDATE `api/main.py` — stop production startup from mutating schema directly. Keep development behavior if needed, but production should rely on an explicit migration/sync command.
- UPDATE `api/core/logic/router_factory.py` — cap `per_page` to a production-safe value and prevent huge list responses.
- UPDATE file upload/import paths (`api/core/lib/storage.py`, `api/core/api/files.py`, `api/core/logic/router_factory.py`) — add upload size/type validation and avoid reading large CSV/upload payloads entirely into memory where feasible.

### Backend Verification

- Run `cd api && python -m pytest -q` if feasible.
- Run targeted checks for auth/scope/report endpoints if tests are too broad.
- Paste command tails and any remaining blockers in the backend agent report.

---

## Frontend Tasks

### Phase 1 — Security UX and Generated UI Robustness

- UPDATE `ui/src/views/WebPageView.tsx` — sanitize CMS HTML before rendering, or render a safe fallback until backend sanitization is available. Do not pass unsanitized database HTML directly to `dangerouslySetInnerHTML`.
- UPDATE `ui/src/lib/api.ts` and `ui/src/store/authStore.ts` only if needed after backend changes — keep token handling compatible, and document remaining `localStorage` risk in the agent report if not changed.
- UPDATE `ui/src/aras-core/components/DynamicForm.tsx` — add request cancellation/stale-response guards for metadata and record loading.
- UPDATE `ui/src/aras-core/components/ListView.tsx` — debounce search and cancel/ignore stale list requests.
- UPDATE `ui/src/aras-core/components/ListView.tsx` — remove client-side `org_id` filter injection and rely on validated backend `X-Org-ID` scope.
- UPDATE shared list/form status UI if touched — extract duplicated status glyph/badge logic only if it is necessary for the requested changes.

### Phase 2 — Mobile Web and PWA Readiness

- UPDATE `ui/index.html` and `ui/public/` — add PWA manifest link, app title, theme color, Apple mobile metadata, and a basic `manifest.webmanifest`.
- ADD or UPDATE service worker/PWA setup only if the existing Vite setup supports it without a large dependency change. If dependency installation is required, document exact package and command instead of installing.
- UPDATE mobile web controls in `ListViewActionBar.tsx` and `DynamicForm.tsx` — ensure touch targets are at least 44x44 below `md`.
- UPDATE mobile input CSS in `ui/src/index.css` — ensure inputs/selects/textareas are at least 16px on mobile to avoid iOS auto-zoom.
- UPDATE layout/header safe-area handling for standalone/mobile web where appropriate.

### Native Mobile Follow-up

- UPDATE `mobile/app.json` and `mobile/src/lib/api.ts` — require production HTTPS API configuration for builds, and add missing app identifiers/scheme/deep-link basics where feasible.
- If mobile native config needs product identifiers the agent cannot safely invent, leave placeholders and report the exact values needed from the owner.

### Frontend Verification

- Run `cd ui && npm run build` if feasible.
- Run `cd ui && npx tsc -p tsconfig.json --noEmit` if feasible.
- If mobile files change, run the available mobile typecheck/build command if present; otherwise report that no script exists.

---
<!-- -- Below this line is filled automatically by multi_agent.py + Claude -- -->

## Agent Reports (2026-05-25)

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
- verdict: <!-- APPROVED / NEEDS-FIX -->
- reviewed_by: Claude Code
- date: <!-- fill -->
- notes: <!-- none or describe -->

## Revision Tasks
<!-- If verdict is NEEDS-FIX, list tasks here then re-run: python tools/multi_agent.py -->
