# Handoff Spec

> Written by: Claude Code (claude-sonnet-4-6)
> Date: 2026-05-17
> Feature: Plan.md Full Build Queue — Backend 0, C1–C3, Backend 3–4, U4, U13, U14, Backend 6, H1–H2, R4, R6, H4, Backend 5+7–14, P1–P5, R1, R5, Backend 9–10, U1, U5, U2–U3, U6, U11

---

## Context
Implement the full prioritized plan.md build queue in order. Complete each group before the next — later groups depend on earlier ones. Agents have `docs/aras.md` and `docs/framework_ref.md` in context.

---

## Group 0 — Foundation (do first, all groups depend on this)

### Backend Tasks

NEW FILE `api/core/exceptions.py` — define `ArasException(Exception)` base with `message: str`, `detail: dict = None`, `status: int = 500`; subclasses: `ValidationException(status=422)`, `ResourceNotFoundException(status=404)`, `PermissionDeniedException(status=403)`, `ConflictException(status=409)`

NEW FILE `api/core/response.py` — define `ok(data=None, message=None) -> dict` returning `{"success": True, "data": data, "message": message, "error": None}` and `err(message: str, detail=None) -> dict` returning `{"success": False, "data": None, "message": None, "error": {"message": message, "detail": detail}}`

UPDATE `api/core/base/router.py` — add FastAPI exception handlers for all `ArasException` subclasses returning `JSONResponse(status_code=exc.status, content=err(exc.message, exc.detail))`; replace any raw `HTTPException` raises in RouterFactory with the appropriate typed exception

---

## Group 1 — Dashboard Correctness (C1–C3)

### Frontend Tasks

UPDATE `ui/src/views/DashboardView.tsx` — **C1**: fix SVG pie `strokeDashoffset` — compute as number first, then pass to attribute (no string concat); **C2**: add `.catch(e => notify(e.message, 'error'))` on every bare `api.get()`/`api.post()` call inside `StatWidget` and `ListWidget`; **C3**: add `loadWidgets` to the `useEffect` dependency array near line 25

---

## Group 2 — M2M + Atomicity (Backend 3, Backend 4, U4, U13)

### Backend Tasks

UPDATE `api/core/base/model.py` — **Backend 3**: in `Model.paginate`, after fetching the page call `resolve_m2m(db, records)` so M2M fields are populated in all list responses

UPDATE `api/core/base/model.py` — **Backend 4**: remove `db.commit()` at lines 478, 553, 556 from `Model.save`; move a single `db.commit()` into `RouterFactory` after each mutating operation (POST, PUT, PATCH, DELETE) so the entire request is one atomic transaction

### Frontend Tasks

UPDATE `ui/src/components/DynamicForm.tsx` — **U4**: replace sequential `POST parent → loop POST children` with a single `/batch` call `{parent: {...}, children: [{resource, data}]}`; display per-child errors on partial failure

UPDATE `ui/src/components/InlineChildTable.tsx` — **U13**: before any save/submit, filter out rows where all user-editable fields are empty/null; toast-warn if rows are discarded; never POST empty rows

---

## Group 3 — Lookup N+1 + Child Hydration (U14, Backend 6)

### Frontend Tasks

UPDATE `ui/src/components/InlineChildTable.tsx` — **U14**: add a module-level `Map<string, Record[]>` lookup cache keyed by `target_resource`; `InlineLookupCombobox` checks cache before calling `api.get(target_resource)`, populates on first miss, invalidates on record save

### Backend Tasks

UPDATE `api/core/base/router.py` (GET `/{id}` handler in RouterFactory) — **Backend 6**: after fetching the parent, detect child_table fields from model metadata; for each, run one batch query `WHERE parent_id = id`; embed as `{field_name: [records]}` in the parent response payload

---

## Group 4 — Quick Wins (H1, H2, R4, R6, H4)

### Frontend Tasks

NEW FILE `ui/src/lib/iconUtils.ts` — **H1**: export `resolveIcon(name: string): LucideIcon` → `(LucideIcons as any)[name] || Package`; update all 8 files that inline this pattern to import from here instead

NEW FILE `ui/src/lib/menuUtils.ts` — **H2**: export `filterMenuItems(items: MenuItem[]): MenuItem[]` applying `!/supplier/i.test(item.label)`; replace all 3 inline call sites

NEW FILE `ui/src/lib/schemaUtils.ts` — **R4**: export `createDefaultRecord(metadata: FieldMeta[]): Record<string, unknown>` handling boolean/date/datetime/number/string defaults; replace identical chains in `DynamicForm.tsx:~262` and `InlineChildTable.tsx:~58`

UPDATE `ui/src/components/InlineChildTable.tsx` — **R6**: replace full `ListToolbar` with a minimal `SubTableToolbar` that only renders "Add Row" + "Delete Selected"; no export/bulkEdit stubs

UPDATE codebase — **H4**: move `ui/src/aras-core/components/DashboardView.tsx` → `ui/src/views/DashboardView.tsx`; update all import paths

---

## Group 5 — Computed Fields + Aggregate + Import Fix (Backend 5, 7, 8)

### Backend Tasks

UPDATE `api/core/ui/generator.py` — **Backend 7**: include `@Aras.computed_field`-decorated fields in `generate_metadata` output with `"computed": true, "read_only": true`

UPDATE `api/core/base/router.py` — **Backend 5**: add `GET /aggregate?field=X&func=sum|count|avg&filters=...` to RouterFactory; execute SQLAlchemy aggregate and return `ok(data={"value": N})`

UPDATE `api/core/base/router.py` — **Backend 8**: ensure `/import` route exists as canonical (add alias or rename `/import-bulk`); `ListView.tsx` calls `/import`

---

## Group 6 — UI Primitives (P1–P5, R1, R5)

### Frontend Tasks

NEW FILE `ui/src/components/Card.tsx` — **P1**: `<Card className?>` renders `div` with `bg-white rounded-xl border border-slate-200 shadow-sm`; replace all 37 inline occurrences

NEW FILE `ui/src/components/PageShell.tsx` — **P2**: `<PageShell>` wraps children in `animate-in fade-in slide-in-from-bottom-4 duration-500`; replace all 10+ inline occurrences

NEW FILE `ui/src/components/LoadingState.tsx` — **P3**: unified spinner/skeleton; replace all 4–5 ad-hoc loading patterns across views

NEW FILE `ui/src/components/EmptyState.tsx` — **P4**: `<EmptyState icon? title description action?>` component; replace inline empty state markup in AppHome, DashboardView, ListView

UPDATE `ui/src/components/MainLayout.tsx`, `ui/src/components/HeaderSearch.tsx`, `ui/src/views/Profile.tsx`, `ui/src/views/GlobalSettings.tsx` — **P5**: replace every `console.error(...)` with `notify(message, 'error')` from `useAras()`

UPDATE `ui/src/lib/api.ts` — **R1**: call `cleanResourcePath` internally on every request path so callers never invoke it manually; remove all manual `cleanResourcePath(...)` call sites across components and hooks

UPDATE `ui/src/views/DashboardView.tsx` — **R5**: replace `if widget_type === 'stat'/'chart'/'list'` chain with a `WidgetRegistry` map `{stat: StatWidget, chart: ChartWidget, list: ListWidget}`; export `WidgetRegistry.register(type, Component)` for custom widgets

---

## Group 7 — API Envelope + Silent Exceptions (Backend 9, 10)

### Backend Tasks

UPDATE all ERP `@Aras.model_action` handlers that return raw values — **Backend 9**: wrap with `response.ok(data=...)` so every action returns the standard envelope

UPDATE `api/core/base/model.py:393` — **Backend 10**: replace bare `except: pass` with `except Exception as e: logger.warning("serialization skipped: %s", e)` so errors appear in logs

---

## Group 8 — Layout + Naming Fixes (Backend 11–14)

### Backend Tasks

UPDATE `api/apps/erp/pot/views.py` — **Backend 11**: audit all views for missing/duplicate `key` field in layout sections; add where absent, deduplicate where repeated

UPDATE `api/core/base/document.py` — **Backend 12**: define constants `DOC_LAYOUT_HEADER` and `DOC_LAYOUT_NOTES`; replace all duplicate header/notes section dicts across document views with these constants

UPDATE `api/apps/erp/accounting/views.py` — **Backend 13**: rename "Totals" tab → "Financials" everywhere; one consistent name for the 3-field financial section

UPDATE `api/apps/erp/` inflow models — **Backend 14**: rename `customer_id` → `party_id` on inflow models to match outflow; add note in output: "run `python manage.py sync`"

---

## Group 9 — UX Features (U1, U5, U2, U3, U6, U11)

### Frontend Tasks

UPDATE `ui/src/components/DynamicForm.tsx` — **U1**: pre-submit validation using field metadata: check `required`, `min`/`max`, `pattern`; block submit and show inline error per field; no server round-trip

UPDATE `ui/src/components/DynamicForm.tsx` — **U5**: for fields where `field_type === 'm2m'` in metadata, render `MultiSelectCombobox`; on save, POST to `/{resource}/{id}/m2m/{field}` with `{add: [...], remove: [...]}` diff

UPDATE `ui/src/views/ListView.tsx` — **U2**: add "Bulk Edit" button in toolbar (visible only when rows are selected); opens a side panel with editable fields; PATCH each selected record on submit; show per-record success/fail feedback

UPDATE `ui/src/components/InlineChildTable.tsx` — **U3**: make cells clickable for simple types (text, number, select, date); click enters inline edit mode with input; Enter/blur saves via PATCH; Escape cancels

NEW FILE `ui/src/views/ArchivedView.tsx` — **U6**: list view calling `GET /{resource}/deleted`; toolbar has "Restore" button calling `POST /{resource}/{id}/restore`; link from ListView via archive icon in toolbar

UPDATE `ui/src/components/CommandPalette.tsx` — **U11**: wire `Cmd+K` globally to open CommandPalette (currently unwired); add a `?` key global handler that opens a modal listing all keyboard shortcuts

---

## Notes for Agents
- Complete groups in order 0 → 9. Later groups depend on earlier ones.
- All new API responses must use `response.ok` / `response.err` from Group 0.
- Backend model changes: note "run `python manage.py sync`" in your output.
- Frontend errors: always use `useAras().notify`, never `console.error`.
- Keep changes targeted — no rewrites of files outside the listed tasks.

---
<!-- ── Below this line is filled automatically by multi_agent.py + Claude ── -->
