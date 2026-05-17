You have to input your plan here. No delete. Add plan, mark done which done.

# Aras Framework — Master Plan

---

## 1. Backend (Sistem)

| # | Item | Status | Effort |
|---|------|--------|--------|
| 0 | Custom Exceptions — centralize `exceptions.py` with ValidationException, ResourceNotFound, etc.; Response Wrapper — `response.py` with standard envelope (success/data/message/error) | ⬜ TODO | Low |
| 1 | Field-level validation — `min/max/pattern` on `Field()` enforced in router before DB write | 🟡 HALF | Low |
| 2 | WebSocket `/ws` — stub exists; NOT pushing audit logs, workflow state, or dashboard changes | 🟡 HALF | Medium |
| 3 | M2M missing in list views — `Model.paginate` skips `resolve_m2m`; M2M fields blank in ListView | ⬜ TODO | Low |
| 4 | Transaction atomicity — `Model.save` calls `db.commit()` at line 478, 553, 556; move commit up to Router/Service layer so actions and batch ops are atomic | ⬜ TODO | Medium |
| 5 | Client-side dashboard aggregation — `ChartWidget` fetches all records and tallies in browser; crashes on large tables; add `/aggregate` endpoint to `RouterFactory` | ⬜ TODO | Medium |
| 6 | N+1 child table fetch — `DynamicForm` loops `api.get(childRes)` for every child_table field on parent load; hydrate child records in parent `GET /{id}` payload instead | ⬜ TODO | Medium |
| 7 | Computed field metadata gap — computed fields in `to_dict` but omitted from `UIGenerator.generate_metadata`; UI won't show them without manual View override | ⬜ TODO | Low |
| 8 | Import endpoint mismatch — `RouterFactory` exposes `/import`, `ListView.tsx` calls `/import-bulk`; one doesn't exist in standard factory | ⬜ TODO | Low |
| 9 | API response envelope inconsistency — custom actions in ERP models return raw values; `RouterFactory` wraps inconsistently | ⬜ TODO | Low |
| 10 | Silent exception swallow — `core/base/model.py:393` bare `except: pass` swallows serialization errors | ⬜ TODO | Low |
| 11 | Layout `key` field — inconsistently present/absent across views; mixed in `pot/views.py` | ⬜ TODO | Low |
| 12 | Layout block deduplication — `DOC_LAYOUT_HEADER`, `DOC_LAYOUT_NOTES` constants in `base/document.py` | ⬜ TODO | Low |
| 13 | Naming inconsistency — "Totals" vs "Financials" tab for same 3 fields in `accounting/views.py` | ⬜ TODO | Low |
| 14 | Field inconsistency — `customer_id` (inflow) vs `party_id` (outflow) for same counterparty | ⬜ TODO | Low |
| 15 | Hook system — `@Aras.on_create/update/delete` hooks don't receive `db` or `user_id`; add both + `@Aras.on_validate` that runs pre-commit and can raise `ValidationException` | ⬜ TODO | Medium |
| 16 | Global search stale ref — `query.py:97` still uses `__title__` attribute (removed); fix via View registry + implement searchable resource index to avoid full-model loop | ⬜ TODO | Low |
| 17 | ResourceRegistry — `UIGenerator` does full app registry scan per FK to resolve resource paths; build centralized map at startup | ⬜ TODO | Low |
| 18 | Icon standard — all ERP views (`accounting`, `asset`, `party`, `config`) use `pi pi-*` PrimeIcons strings; frontend resolves via Lucide; replace all with Lucide names | ⬜ TODO | Low |
| 19 | Seed framework — seeding scattered across `seed_coa.py`, `seed_series.py`, `seed_random_invoices.py`, `seed_basic.py`; standardize `App.seed(db)` method called by `manage.py seed` | ⬜ TODO | Low |

---

## 2. Frontend (UI)

### 2a. Correctness Bugs

| # | Item | Status | Effort |
|---|------|--------|--------|
| C1 | `DashboardView.tsx` SVG pie — `strokeDashoffset` string concat produces invalid SVG attribute | ⬜ TODO | Low |
| C2 | `StatWidget`/`ListWidget` — no `.catch()` on API calls; silent failures leave widget stuck | ⬜ TODO | Low |
| C3 | `DashboardView.tsx:~25` — `useEffect` missing `loadWidgets` dep; `react-hooks/exhaustive-deps` violation | ⬜ TODO | Low |

### 2b. Maintainability

| # | Item | Status | Effort |
|---|------|--------|--------|
| H1 | `resolveIcon()` — `(LucideIcons as any)[name] \|\| Package` copy-pasted in 8 files → `lib/iconUtils.ts` | ⬜ TODO | Low |
| H2 | `filterMenuItems()` — `!/supplier/i.test(...)` hardcoded in 3 files → `lib/menuUtils.ts` | ⬜ TODO | Low |
| H3 | `FieldProps` in `SchemaRegistry.tsx` — `value/onChange/field/formData` all `any`; drives 102 downstream `any` uses | ⬜ TODO | High |
| H4 | `DashboardView.tsx` is a page view living in `aras-core/components/` — move to `views/` | ⬜ TODO | Low |

### 2c. UX Features

| # | Item | Impact | Status | Effort |
|---|------|--------|--------|--------|
| U1 | Client-side form validation — pre-submit using field metadata (required, min/max, pattern) | High | ⬜ TODO | Low |
| U2 | Bulk edit modal — bulk field-update for selected rows in ListView | High | ⬜ TODO | Medium |
| U3 | Inline row editing — click cell to edit in-place for simple fields | High | ⬜ TODO | Medium |
| U4 | Atomic batch save — new record + child rows POSTs parent then loops children; partial failure leaves orphan; use `/batch` for atomic parent+children | High | ⬜ TODO | Medium |
| U5 | M2M UI — `MultiSelectCombobox` exists but `DynamicForm` only handles child_table (1:M), not bridge-table updates for M2M | High | ⬜ TODO | Medium |
| U6 | Soft-delete bin — backend `/deleted` + restore exist; no UI to view or restore archived records | Medium | ⬜ TODO | Low |
| U7 | Column visibility storage — currently `localStorage`; persist as `UserPreference` model in backend for multi-device admin | Medium | ⬜ TODO | Medium |
| U8 | Dark mode — toggle + store wired ✅; `dark:` Tailwind classes cover only 2 files (95% of UI unaffected) | Medium | 🟡 HALF | High |
| U9 | Dashboard drag-to-rearrange — widget reorder exists but uses index-swap only (no splice/move) | Medium | 🟡 HALF | Medium |
| U10 | Column resizing & freeze — fixed-width columns; freeze col 1 + drag-to-resize | Medium | ⬜ TODO | Medium |
| U11 | Keyboard shortcut map — `?` key shows all shortcuts; `Cmd+K` not wired to CommandPalette | Medium | ⬜ TODO | Low |
| U12 | Profile edit — name/email display-only; no edit mode (change-password exists) | Low | ⬜ TODO | Low |
| U13 | Inline table ghost rows — "Add Row" pushes blank dict; saving without filling triggers confusing 422 on child fields; validate/discard empty rows before save | Medium | ⬜ TODO | Low |
| U14 | Lookup N+1 in InlineChildTable — `InlineLookupCombobox` calls `api.get(target_resource)` per row; 50 rows with same lookup = 50 requests; add React Context cache for lookup dictionaries | High | ⬜ TODO | Medium |
| U15 | Metadata-driven tabs — forms with many sections stack vertically; add tab support to `View.layout` so `DynamicForm` renders multi-tab interfaces | Medium | ⬜ TODO | Medium |
| U16 | Flexible grid layout — `DynamicForm` hardcoded 2-column grid; add `col_span` to `LayoutSection` field definitions for full-width fields and 3-column grids | Medium | ⬜ TODO | Low |
| U17 | Command Palette action search — `Cmd+K` only searches records; add "Action Search" (e.g., "New Invoice", "Go to Settings") for keyboard-driven navigation | Medium | ⬜ TODO | Low |
| U18 | Hardcoded field logic in `DynamicForm` — `profile`, `org_id`, `unit_type` handled via `if field.name ===` at lines 634–636; move into metadata system (specialized UI types or choices) | Medium | ⬜ TODO | Medium |
| U19 | Form Settings panel — SidePanel-over-ListView approach (no dedicated `/settings/:resource` page); accessible from gear icon in DynamicForm header and "Settings" button in ListView toolbar; supports tabbed layout for Fields/Layout/Columns/Permissions | High | ⬜ TODO | Medium |
| U20 | Form Settings tabs — Form Settings page has tabbed layout: **Fields** (label, required, hidden, read-only, default_value, series override per `FieldModel`), **Layout** (drag-and-drop form builder), **List Columns** (column order/visibility), **Permissions** (per-role field visibility) | High | ⬜ TODO | High |
| U21 | Drag-and-drop Form Builder — "Layout" tab in Form Settings; drag fields into sections/tabs, reorder sections; persists to `ResourceModel.layout` JSON; `DynamicForm` reads this layout at runtime instead of `View.layout` from code | High | ⬜ TODO | High |

### 2d. UI Primitives / Shared Components

| # | Item | Status | Effort |
|---|------|--------|--------|
| P1 | `<Card>` — `bg-white rounded-3xl border border-slate-200 shadow-sm` repeated 37× | ⬜ TODO | Low |
| P2 | `<PageShell>` — `animate-in fade-in slide-in-from-bottom-4 duration-500` repeated 10×+ | ⬜ TODO | Low |
| P3 | `<LoadingState>` — 4–5 different loading patterns across views; no shared component | ⬜ TODO | Low |
| P4 | `<EmptyState>` — inline empty state markup repeated across AppHome, DashboardView, ListView | ⬜ TODO | Low |
| P5 | Error notifications — `console.error` in `MainLayout:28`, `HeaderSearch:38`, `Profile:23`, `GlobalSettings:32,71` never reaches `notify()` | ⬜ TODO | Low |

### 2e. Repeatables / Tech Debt

| # | Item | Status | Effort |
|---|------|--------|--------|
| R1 | `cleanResourcePath` overuse — manually called in almost every component/hook; abstract into api client or `useResource` hook | ⬜ TODO | Low |
| R2 | Service vs. logic location — ERP services (`recalc_mixin.py`, `posting.py`) mixed with models; standardize `services/` folder for all apps | ⬜ TODO | Low |
| R3 | Circular import fatigue — local imports inside methods across `model_actions.py`, `model.py`, app actions; introduce `ServiceRegistry`/`DependencyProvider` | ⬜ TODO | High |
| R4 | `createEmptyRecord` boilerplate — identical `if type==='boolean'`/`date`/`datetime` chains in `DynamicForm.tsx:~262` and `InlineChildTable.tsx:~58`; extract to `SchemaRegistry.createDefaultRecord(metadata)` | ⬜ TODO | Low |
| R5 | Hardcoded widget registry — `DashboardView.tsx:87–89` uses `if widget_type==='stat'/'chart'/'list'`; replace with `WidgetRegistry` pattern so app modules inject custom widgets | ⬜ TODO | Low |
| R6 | `<SubTableToolbar>` — `InlineChildTable.tsx:78–88` uses full `ListToolbar` with empty stubs (`onExport/onBulkEdit={() => {}}`); needs a dedicated lightweight toolbar | ⬜ TODO | Low |

---

## 3. Framework Refactoring

### Phase 1 — Utility Centralization
Move label formatting (`.replace("_", " ").title()`) from `UIGenerator`, `App`, and `View` into `Aras.helper.to_label_case(name)` in `api/core/lib/helpers.py`. Ensures consistent naming across UI, menus, and breadcrumbs.

### Phase 2 — Modular UIGenerator
Refactor `UIGenerator.generate_metadata` to a Type Handler Pattern — registry of small handler functions (`_handle_lookup`, `_handle_select`, `_handle_numeric`) replacing the large `if/elif` block. Makes adding new field types (Signature, RichText) safe without touching core.

### Phase 3 — Model & View Enhancements
1. `Aras.Model.get_ui_fields()` — standardize retrieval of non-system visible columns.
2. Metadata Cache — in-memory dict with flush mechanism in `UIGenerator` to avoid repeated DB queries during high-load UI rendering.

### Phase 4 — Developer Experience
`/api/v1/dev/metadata/flush` endpoint to clear metadata cache during active development. Ensures model/view changes appear immediately without restart.

---

## 4. GUI Redesign (Admin Operator Focus)

Goal: dense, reliable admin workflows — faster scanning, clearer actions, better responsive behavior, less decorative visual weight. No backend API or metadata schema changes. No route changes.

### Key Changes
- **Shared UI primitives** — buttons, inputs, cards, page headers, empty states, status badges, dialogs, side panels; replace repeated Tailwind one-offs with `rounded-lg/rounded-xl` instead of `rounded-3xl/rounded-[2.5rem]`
- **App shell** — responsive sidebar, auto-expand active section, collapsed-state tooltips, tighter header, global search usable on narrow screens
- **CRUD list views** — compact toolbar, persistent bulk-action bar, clearer filter builder, robust empty/loading/error states, better zero-record pagination copy, accessible column picker, row keyboard/focus, horizontal table on mobile
- **Dynamic forms** — quieter sticky action bar, clearer section hierarchy, consistent field spacing, better validation placement, accessible required/read-only states, less visual nesting for child tables
- **Dashboard/settings/dev pages** — replace marketing cards and decorative blobs with operational panels, tighter grids, clear primary actions, status-oriented summaries
- **Overlays** — dialogs and side panels keyboard-dismissible, focus-trapped, screen-reader labeled, visually consistent
- **UX bug fixes** — global search route fallback, inactive Configure/delete app card buttons, icon-only buttons without labels, inconsistent alert vs dialog system usage

### Test Plan
- `npm run build` and `npm run lint` in `ui/`
- Manual verify: `/`, `/settings`, `/apps`, `/dev`, `/settings/rbac`, dynamic list routes, dynamic edit/new routes, login, dialogs, side panels
- Widths: desktop, tablet, mobile — sidebar, header search, tables, forms, modals, child table sections
- Keyboard: tab order, Escape closes overlays, Enter/Space activate controls, visible focus
- Admin workflows: search, filters, sort, pagination, column toggles, bulk delete confirm, import/export, form save/cancel, action dialogs, child record creation

---

## 5. Recommended Build Order

0. **Backend 0** — Custom Exceptions + Response Wrapper (foundation for all error handling)
1. **C1–C3** — Dashboard correctness bugs (fix before any dashboard work)
2. **Backend 3** — M2M in paginate (data correctness, affects all list views)
3. **Backend 4** — Transaction atomicity: remove `db.commit()` from `Model.save`, move to Router/Service layer
4. **U4** — Atomic batch save for parent+children (pairs with Backend 4)
5. **U13** — Ghost row validation before save (quick UX win, pairs with U4)
6. **U14** — Lookup N+1 cache in InlineChildTable (performance, unblocks complex docs)
7. **Backend 6** — N+1 child table fetch: hydrate in parent GET payload
8. **H1** `resolveIcon()` + **H2** `filterMenuItems()` — quick wins, unblock future views
9. **R4** `SchemaRegistry.createDefaultRecord()` — eliminate boilerplate in DynamicForm + InlineChildTable
10. **R6** `<SubTableToolbar>` — replace ListToolbar stubs in InlineChildTable
11. **H4** move `DashboardView.tsx` to `views/`
12. **Backend 5** / **Backend 7** — Computed field metadata + `/aggregate` endpoint
13. **Backend 8** — Import endpoint mismatch fix
14. **P1–P4** `<Card>` + `<PageShell>` + `<LoadingState>` + `<EmptyState>`
15. **P5** + **R1** — error notifications + `cleanResourcePath` into api client
16. **R5** WidgetRegistry pattern for DashboardView
17. **Backend 9–10** — API envelope consistency + silent exception fix
18. **Backend 11–14** — Layout key, deduplication, naming fixes
19. **U1** client-side form validation
20. **U5** M2M UI in DynamicForm
21. **U2–U3** bulk edit + inline row editing
22. **U6** soft-delete bin UI
23. **U11** `Cmd+K` wire-up + `?` shortcut map
24. **Backend 1** field-level validation enforcement in router
25. **Backend 2** WebSocket real-time push
26. **U7** column visibility → UserPreference backend
27. **R2** services/ folder standardization
28. **R3** ServiceRegistry / circular import fix (large)
29. **U8** dark mode systematic pass (large)
30. **H3** `FieldProps` typing (large)
31. **U10** column resizing & freeze
32. **U15** metadata-driven tabs in DynamicForm
33. **U16** flexible grid layout (`col_span` support)
34. **U18** hardcoded field logic → metadata system
35. **U19** Form Settings panel (SidePanel with tabs)
36. **U20** Form Settings tabs (Fields, Layout, Columns, Permissions)
37. **U21** drag-and-drop Form Builder in Layout tab
38. **U17** Command Palette action search (Cmd+K)
39. **Backend 15** hook system (`@Aras.on_validate`, add `db`/`user_id`)
40. **Backend 16** global search stale ref + searchable resource index
41. **Backend 17** ResourceRegistry centralized map at startup
42. **Backend 18** icon standard (PrimeIcons → Lucide)
43. **Backend 19** seed framework standardization
44. **Framework 1–4** refactoring phases
45. **GUI Redesign** full admin UI overhaul
