> Written by: Claude Code (claude-opus-4-7)
> run_id: 100
> Date: 2026-05-28
> Feature: Full sweep — immediate UX fixes + P0 in-flight close-out + P1 polish + P2 backend quality + P3 docs
> Mode: AUTORUN via tools/autorun_handoff.sh (splits this spec into 6 batches, runs multi_agent per batch). Each AI batch prompt ENDS with `/clear` instruction so context resets per-AI after every task.

## Context
Comprehensive cleanup pass: closes mid-flight refactor (UserPreference, M2M endpoint, metadata cache, WS listener, FormSettings precedence, ActionBar dedup, inline-edit hardening), lands three immediate UX fixes (theme lift to all routes, DB-driven public landing, Template Studio current-page memory), then UI/UX polish (dirty-state guard, a11y, responsive tables, typography scale, data-driven CommandPalette, error UX), backend quality (split oversized files, Service base, test scaffolding, attribution audit), and docs sync.

---

## BATCH 1 — Immediate UX fixes (theme + landing + template studio)

### Backend Tasks
- UPDATE `api/apps/web/routers.py` — add `GET /web/landing/{key}` returning a single section (404 if missing). Keep list endpoint untouched.
- UPDATE `api/apps/web/models.py` — add `@Aras.model_action(name="reorder", permission="edit")` on `LandingSection` accepting `{"sort_order": int}` and persisting.
- UPDATE `api/apps/web/views.py` — add `Aras.View` for `LandingSection` with `title="Landing Sections"`, `icon="pi pi-image"`, two-tab layout: `General` (key, title, subtitle, body, is_visible, sort_order) and `Media & CTA` (image_url, cta_label, cta_url).
- NEW FILE `api/apps/web/seed_landing.py` — idempotent (upsert by `key`) seeder for: `hero`, `feature.pos`, `feature.stock`, `feature.report`, `testimonial.one`, `testimonial.two`, `cta`. Callable as `python apps/web/seed_landing.py` and from installer.
- UPDATE `api/core/api/dev.py` — add `GET /dev/dev_template_trees/list` returning `[{template_name, updated_at}]`.
- Run `python manage.py sync` after model/view changes.

### Frontend Tasks
- UPDATE `ui/src/App.tsx` — lift theme CSS-var effect to top-level `useEffect` in `App()`, reading `themeMode, cornerMode, density, fontScale, accentColor` from `useUIStore` and writing `--accent`, `--aras-accent`, `--aras-accent-strong`, `--aras-accent-glow`, `--aras-radius`, `--aras-radius-lg`, `--aras-density`, `--aras-font-scale` to `document.documentElement.style` + toggling `.dark` class + `data-theme`. Must run on login/public/portal routes too.
- UPDATE `ui/src/layouts/MainLayout.tsx` — remove duplicate theme `useEffect` (L33–45). Keep `style={layoutStyle}` on root div.
- UPDATE `ui/src/views/PublicLanding.tsx` — fetch `GET /web/landing`. Map sections by key (`hero`, `feature.*`, `testimonial.*`, `cta`) into existing render. Keep pricing block from `/saas/plans/public`. Keep i18n fallback when API empty/fails. Add "Edit page" floating link (bottom-right) when `useAuthStore().user?.is_superuser` linking to `/erp/web/landing-sections` and `/dev/template-builder?from=landing`.
- UPDATE `ui/src/views/TemplateBuilder.tsx` — current-page memory:
  1. If `searchParams.get('from')` missing → read `localStorage.getItem('template-studio:last')`; fall back `DEFAULT_TEMPLATE_NAME` only if both missing.
  2. After `loadTree` success → `localStorage.setItem('template-studio:last', fromRoute)`.
  3. After `handleSave` success → persist last.
  4. Fetch `GET /dev/dev_template_trees/list` and pass `availableTemplates` to Topbar.
- UPDATE `ui/src/views/template-studio/panels/Topbar.tsx` — add `SimpleCombobox` of `availableTemplates`. On select → `navigate(?from=<name>)`. Show "Current: <name>" label.
- UPDATE `ui/src/views/DevTools.tsx` (L308–315) — launcher chooses last-used:
  ```ts
  const last = localStorage.getItem('template-studio:last') || ''
  const ref = (() => { try { const u = new URL(document.referrer); return u.origin === location.origin ? u.pathname : '' } catch { return '' } })()
  const from = ref || last
  navigate(from ? `/dev/template-builder?from=${encodeURIComponent(from)}` : '/dev/template-builder')
  ```
- UPDATE `ui/src/layouts/components/TemplateDesignToggle.tsx` — before navigating, `localStorage.setItem('template-studio:last', location.pathname)`.
- UPDATE `ui/src/views/Login.tsx` — add `data-testid="login-card"`; no logic change.

### Verification
1. Tweak accent → "Pine" → log out → Login button is pine.
2. `curl /api/v1/web/landing` ≥4 sections after seed.
3. Edit `hero.title` in `/erp/web/landing-sections` → `/welcome` updated, no code change.
4. DevTools "Template Builder" → loads last template, not default.
5. Topbar combobox switches templates and URL updates.

### End-of-batch (each AI must do this)
1. Append your file list to `docs/handoff.md` under `## Agent Reports`.
2. Append entry to `docs/feature.md` (if new feature) or `docs/fix.md` (if bug fix), one bullet per file, tagged with your model name.
3. Run `/clear` to reset your conversation context before exiting. This is MANDATORY — next batch will start fresh.

---

## BATCH 2 — Priority 0a: UserPreference + M2M + metadata cache

### Backend Tasks
- UPDATE `api/core/auth/models.py` — confirm `UserPreference(user_id FK, key str, value JSON, unique=(user_id,key))`. Add if missing.
- UPDATE `api/core/auth/routes.py` — `GET /preference?key=`, `PUT /preference` body `{key,value}` — both scoped by `current_user.id` only (NEVER trust client-supplied user_id).
- UPDATE `api/core/manager/installer.py` — include UserPreference in auto-create.
- UPDATE `api/core/logic/router_factory.py` — M2M endpoint `PUT /{item_id}/{m2m_field}` body `List[int]`:
  - Validate target IDs exist AND are in scope (reject 400 with detail on any mismatch — no silent skip; matches 2026-05-26 hardening).
  - After commit, call `broadcast_sync({"event":"m2m_update","resource":<table>,"id":<item_id>,"field":<m2m_field>})`.
- UPDATE `api/core/logic/ui_generator.py` — cache key tuple `(resource, lang, org_id)`. Add `invalidate(resource)` method.
- UPDATE `api/core/logic/router_factory.py` — after POST/PUT to `aras_resources` or `aras_fields`, call `UIGenerator.invalidate(target_resource_name)`.
- Run `python manage.py sync`.

### Frontend Tasks
- UPDATE `ui/src/lib/ws.ts` — robust connect: read `useAuthStore.getState().token`; reconnect with exponential backoff (1s, 2s, 4s, max 30s); emit `CustomEvent('aras:record-event', {detail})`. Only connect when token exists.
- UPDATE `ui/src/main.tsx` — call `connectArasWebSocket()` AFTER auth bootstrap (move inside `App.tsx` useEffect gated on `token`), not at module top-level.
- UPDATE `ui/src/aras-core/components/FormSettings.tsx` — after save, call `await api.post('/dev/metadata/flush', {resource})` to invalidate backend cache.

### Verification
1. `cd api && python manage.py sync` → UserPreference table exists.
2. `PUT /api/v1/<app>/<res>/{id}/<m2m_field>` body `[9999]` (nonexistent) → 400.
3. Edit field in FormSettings → next `/metadata` GET reflects without server restart.
4. Two browser tabs logged in → m2m write in tab A → tab B receives WS event.

### End-of-batch (each AI must do this)
1. Append file list to `docs/handoff.md` under `## Agent Reports`.
2. Append `docs/feature.md` / `docs/fix.md` entry.
3. Run `/clear` to reset context. MANDATORY.

---

## BATCH 3 — Priority 0b: WS listener + FormSettings precedence + inline-edit + ActionBar dedup

### Frontend Tasks
- UPDATE `ui/src/aras-core/components/ListView.tsx`:
  - Subscribe to `window.addEventListener('aras:record-event', handler)`. When `detail.resource === currentResource`, refetch current page (debounced 200ms).
  - Column state read/write `UserPreference` key `list:{resource}:columns` via `/preference`.
  - Inline cell edit: replace bare `<input>` with `SchemaRegistry.renderField(fieldMeta, value, onChange)` in edit mode. Validate per-cell using lifted `validateField`. Keyboard: Esc=cancel, Enter=commit+next-row, Tab=commit+next-cell, blur=commit.
- UPDATE `ui/src/aras-core/components/DynamicForm.tsx`:
  - Subscribe `aras:record-event`. If `detail.resource === resource && detail.id === recordId` → show banner "Record updated externally — reload?" with Reload button.
  - Extract `validateField(meta, value)` into NEW FILE `ui/src/aras-core/lib/validate.ts`. Import from both DynamicForm and ListView.
- UPDATE `ui/src/aras-core/components/FormSettings.tsx`:
  - "Layout" and "Permissions" tabs gated `user.is_superuser || user.is_admin`.
  - "List Columns" tab: show org default (from ResourceModel) + per-user override toggle (writes UserPreference).
- DELETE `ui/src/aras-core/components/ListViewActionBar.tsx` re-export shim. Update all imports to `import { ArasActionBar } from './ArasActionBar'` with `variant="full"`.
- NEW FILE `ui/src/aras-core/lib/listActions.ts` — move export CSV, import CSV, bulk delete, bulk archive helpers out of inline JSX. Used by ArasActionBar.

### Verification
1. Edit row in tab A → tab B refetches list within 1s.
2. Open form in tab A, update in tab B → tab A shows reload banner.
3. Non-admin user opens FormSettings → Layout/Permissions tabs hidden.
4. Inline-edit a number cell → tab to next cell commits, Esc cancels.
5. `grep ListViewActionBar ui/src` → no matches except deleted file.

### End-of-batch (each AI must do this)
1. Append file list to `docs/handoff.md` under `## Agent Reports`.
2. Append `docs/feature.md` / `docs/fix.md` entry.
3. Run `/clear` to reset context. MANDATORY.

---

## BATCH 4 — Priority 1: UX polish (dirty-state, a11y, responsive, typography, palette, errors)

### Backend Tasks
- NEW FILE `api/core/api/admin.py` (or extend existing) — `GET /admin/quick-actions` returning `[{id, label, kind:"action"|"resource"|"route", target, icon, app}]` filtered by RBAC. Aggregate from: registered `@Aras.model_action` (via `Model._actions`), recent resources accessed (via UserPreference history), RBAC-filtered routes.

### Frontend Tasks
- UPDATE `ui/src/aras-core/components/DynamicForm.tsx`:
  - Track `initialValues` snapshot on load; expose `isDirty = !deepEqual(values, initialValues)`.
  - Register dirty state in `useUIStore.dirtyForms: Set<string>` keyed by `${resource}:${id}`.
- UPDATE `ui/src/store/uiStore.ts` — add `dirtyForms: Set<string>`, `setDirty(key,bool)`.
- UPDATE `ui/src/layouts/MainLayout.tsx` — `useBlocker` (react-router) when `dirtyForms.size > 0`; on block, show `showConfirm("Unsaved changes", "Leave anyway?", proceed, cancel)`.
- UPDATE `ui/src/aras-core/components/ArasTable.tsx`:
  - Add `role="table"`, `<th scope="col">`, `aria-sort={sortDir}`.
  - Arrow-key cell navigation (Up/Down/Left/Right between focusable cells).
  - Below `md` breakpoint (use `window.matchMedia`) render rows as stacked cards (label/value pairs from visible columns); preserve row-click navigation.
  - Sticky first column on `sm` with right-edge box-shadow as scroll indicator.
- UPDATE `ui/src/aras-core/components/DynamicForm.tsx` — `aria-invalid={!!error}`, `aria-describedby={errorId}` per field. On submit with errors, focus first invalid input.
- UPDATE `ui/src/aras-core/components/CommandPalette.tsx`:
  - `role="combobox"`, `aria-controls`, `aria-activedescendant` on input.
  - Replace hardcoded `ACTIONS` array with `useQuery` against `/admin/quick-actions`; cache 60s in-memory; fuzzy-search client-side.
- UPDATE `ui/src/index.css`:
  - Add `:root { --fs-xs: calc(10px * var(--aras-font-scale,1)); --fs-sm: calc(12px * ...); --fs-base: calc(13px * ...); --fs-md: calc(14px * ...); }`.
  - Restore focus-visible ring: `*:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }`.
- Replace hardcoded `text-[10px]/[12px]/[13px]` in ListView, ArasTable, ArasActionBar, Sidebar, Header with `style={{fontSize:'var(--fs-xs)'}}` etc.
- UPDATE `ui/src/aras-core/lib/api.ts` — on error, attach `error.code` from response body. `useAras().notify` extended to accept `{retry?: () => void}`; render retry chip when present.
- UPDATE `ui/src/aras-core/components/DynamicForm.tsx` — pattern validation error reads `field.info?.pattern_hint` (fallback: "Format is invalid").
- NEW FILE `ui/src/components/SkeletonRow.tsx` and `ui/src/components/EmptyState.tsx` (if not extracted) — shared by ListView, InlineChildTable, ArasTable, DashboardView. Consolidate existing duplicates.

### Verification
1. Edit a form, navigate away → confirm dialog appears.
2. Tab into ArasTable → focus visible, arrows nav cells, Enter sorts header.
3. Resize 375px → list renders stacked cards, no horizontal overflow.
4. Submit form with bad email → first invalid input focused, screen-reader announces.
5. Cmd-K → list comes from `/admin/quick-actions`.
6. Slide font-size to 116% in tweak panel → ListView/ArasTable scale visibly.
7. Trigger network error → toast shows "Retry" chip that re-executes.

### End-of-batch (each AI must do this)
1. Append file list to `docs/handoff.md` under `## Agent Reports`.
2. Append `docs/feature.md` / `docs/fix.md` entry.
3. Run `/clear` to reset context. MANDATORY.

---

## BATCH 5 — Priority 2: Backend quality (splits + Service base + tests + attribution)

### Backend Tasks
- SPLIT `api/core/logic/router_factory.py` (951 LOC) into package:
  - `api/core/logic/router_factory/__init__.py` (re-exports `RouterFactory` class)
  - `crud.py` — list/get/create/update/delete mixins
  - `bulk.py` — bulk-delete, batch operations
  - `m2m.py` — m2m field endpoint
  - `aggregate.py` — `/aggregate` endpoint
  - `search.py` — `/search`, `/lookup` endpoints
  Public API: `from core.logic.router_factory import RouterFactory` unchanged.
- SPLIT `api/core/base/model.py` (806 LOC) into package:
  - `api/core/base/model/__init__.py` (re-exports `Model`)
  - `queries.py` — paginate, apply_filters, query helpers
  - `hooks.py` — before_save, after_save, on_create/update/delete
  - `serialization.py` — to_dict, from_dict, Pydantic adapters
- NEW FILE `api/core/base/service.py` — `class Service` with: `list(filters,page,size,sort)`, `get(id)`, `create(payload)`, `update(id,payload)`, `delete(id)`. Each calls RBAC check + audit hook. Refactor `api/apps/accounting/services/*.py`, `api/apps/stock/services/*.py`, `api/apps/saas/services/*.py` to inherit.
- NEW FILES `api/tests/conftest.py` — fixtures `client` (TestClient), `db` (transactional session), `admin_user`, `org`, `auth_headers(user)`. Per-app smoke tests:
  - `api/apps/notes/tests/test_smoke.py` — CRUD Note, RBAC denial, scope leak attempt.
  - `api/apps/accounting/tests/test_smoke.py` — Account CRUD, m2m write.
  - `api/apps/saas/tests/test_smoke.py` — Plan list, Subscription create.
  - `api/apps/web/tests/test_smoke.py` — Landing fetch, page publish action.
- ATTRIBUTION AUDIT — script: grep `^def \|^class ` in `api/`, find functions/classes lacking preceding `# <model>` comment; backfill with `# unknown (needs review)`. Output report `docs/attribution_audit.md`.

### Verification
1. `from core.logic.router_factory import RouterFactory` works (no import errors).
2. `from core.base.model import Model` works.
3. `cd api && pytest -q` → all smoke tests pass.
4. `grep -L "# claude\|# gemini\|# gpt\|# antigravity\|# unknown" api/**/*.py | wc -l` → 0 files with untagged functions.

### End-of-batch (each AI must do this)
1. Append file list to `docs/handoff.md` under `## Agent Reports`.
2. Append `docs/feature.md` / `docs/fix.md` entry.
3. Run `/clear` to reset context. MANDATORY.

---

## BATCH 6 — Priority 3: Docs sync + reports

### Backend Tasks
- UPDATE `docs/framework_ref.md` — refresh all line-number tables affected by router_factory and model splits.
- UPDATE `docs/aras.md` — fix all `→ framework_ref.md L…` pointers to match new line numbers.
- UPDATE `docs/feature.md` — append entries for: UserPreference, M2M endpoint, metadata cache invalidation, FormSettings, ArasTable, ArasActionBar, WebSocket bridge, Landing seeder, quick-actions endpoint, Service base class.
- UPDATE `docs/fix.md` — append: theme propagation to public routes, template studio current-page memory, public landing DB-driven.
- UPDATE `docs/reports.json` — append one entry per completed batch (id = last+1, date 2026-05-28, verdict APPROVED).

### Verification
1. `grep -n "L[0-9]" docs/aras.md | wc -l` — every pointer matches a real line.
2. `python -c "import json; json.load(open('docs/reports.json'))"` parses clean.
3. `docs/feature.md` last 6 entries reference batches 1-6.

### End-of-batch (each AI must do this)
1. Append file list to `docs/handoff.md` under `## Agent Reports`.
2. Append `docs/feature.md` / `docs/fix.md` entry.
3. Run `/clear` to reset context. MANDATORY.

---

## Autorun protocol

- `tools/autorun_handoff.sh` slices this spec by `## BATCH N` headers, writes one batch at a time to a temp `docs/handoff.md`, runs `python tools/multi_agent.py`, then proceeds to next batch.
- Each AI (Gemini backend, Codex frontend) MUST run `/clear` at the end of every batch per its own End-of-batch checklist. This isolates context per task instead of carrying accumulated state across the full sweep.
- After ALL batches: print combined verdict. Stop on first NEEDS-FIX from `rhf` and require human review.
