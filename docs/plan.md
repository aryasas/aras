You have to input your plan here. No delete. Add plan, mark done which done.

# Aras Framework — Master Plan

---

## 1. Backend (Sistem)

| # | Item | Status | Effort |
|---|------|--------|--------|
| 0 | Custom Exceptions — centralize `exceptions.py` with ValidationException, ResourceNotFound, etc.; Response Wrapper — `response.py` with standard envelope (success/data/message/error) | ✅ DONE | Low |
| 1 | Field-level validation — `min/max/pattern` on `Field()` enforced in router before DB write | ✅ DONE | Low |
| 2 | WebSocket `/ws` — stub exists; pushing record_created/updated/deleted events | ✅ DONE | Medium |
| 3 | M2M missing in list views — `Model.paginate` skips `resolve_m2m`; M2M fields blank in ListView | ✅ DONE | Low |
| 4 | Transaction atomicity — `Model.save` calls `db.commit()` at line 478, 553, 556; move commit up to Router/Service layer so actions and batch ops are atomic | ✅ DONE | Medium |
| 5 | Client-side dashboard aggregation — `ChartWidget` fetches all records and tallies in browser; crashes on large tables; add `/aggregate` endpoint to `RouterFactory` | ✅ DONE | Medium |
| 6 | N+1 child table fetch — `DynamicForm` loops `api.get(childRes)` for every child_table field on parent load; hydrate child records in parent `GET /{id}` payload instead | ✅ DONE | Medium |
| 7 | Computed field metadata gap — computed fields in `to_dict` but omitted from `UIGenerator.generate_metadata`; UI won't show them without manual View override | ✅ DONE | Low |
| 8 | Import endpoint mismatch — `RouterFactory` exposes `/import`, `ListView.tsx` calls `/import-bulk`; one doesn't exist in standard factory | ✅ DONE | Low |
| 9 | API response envelope inconsistency — custom actions in ERP models return raw values; `RouterFactory` wraps inconsistently | ✅ DONE | Low |
| 10 | Silent exception swallow — `core/base/model.py:393` bare `except: pass` swallows serialization errors | ✅ DONE | Low |
| 11 | Layout `key` field — inconsistently present/absent across views; mixed in `pot/views.py` | ✅ DONE | Low |
| 12 | Layout block deduplication — `DOC_LAYOUT_HEADER`, `DOC_LAYOUT_NOTES` constants in `base/document.py` | ✅ DONE | Low |
| 13 | Naming inconsistency — "Totals" vs "Financials" tab for same 3 fields in `accounting/views.py` | ✅ DONE | Low |
| 14 | Field inconsistency — `customer_id` (inflow) vs `party_id` (outflow) for same counterparty | ✅ DONE | Low |
| 15 | Hook system — `@Aras.on_create/update/delete` hooks don't receive `db` or `user_id`; add both + `@Aras.on_validate` that runs pre-commit and can raise `ValidationException` | ✅ DONE | Medium |
| 16 | Global search stale ref — `query.py:97` still uses `__title__` attribute (removed); fixed via View registry lookup | ✅ DONE | Low |
| 17 | ResourceRegistry — `UIGenerator` does full app registry scan per FK to resolve resource paths; built centralized map at startup in `ServiceRegistry` | ✅ DONE | Low |
| 18 | Icon standard — all ERP views (`accounting`, `asset`, `party`, `config`) use `pi pi-*` PrimeIcons strings; replaced all with Lucide names | ✅ DONE | Low |
| 19 | Seed framework — seeding scattered; standardized `App.seed(db)` method called by `manage.py seed` | ✅ DONE | Low |

---

## 2. Frontend (UI)

### 2a. Correctness Bugs

| # | Item | Status | Effort |
|---|------|--------|--------|
| C1 | `DashboardView.tsx` SVG pie — `strokeDashoffset` string concat produces invalid SVG attribute | ✅ DONE | Low |
| C2 | `StatWidget`/`ListWidget` — no `.catch()` on API calls; silent failures leave widget stuck | ✅ DONE | Low |
| C3 | `DashboardView.tsx:~25` — `useEffect` missing `loadWidgets` dep; `react-hooks/exhaustive-deps` violation | ✅ DONE | Low |

### 2b. Maintainability

| # | Item | Status | Effort |
|---|------|--------|--------|
| H1 | `resolveIcon()` — `(LucideIcons as any)[name] \|\| Package` copy-pasted in 8 files → `lib/iconUtils.ts` | ✅ DONE | Low |
| H2 | `filterMenuItems()` — `!/supplier/i.test(...)` hardcoded in 3 files → `lib/menuUtils.ts` | ✅ DONE | Low |
| H3 | `FieldProps` in `SchemaRegistry.tsx` — `value/onChange/field/formData` all `any`; drives 102 downstream `any` uses | ✅ DONE | High |
| H4 | `DashboardView.tsx` is a page view living in `aras-core/components/` — move to `views/` | ✅ DONE | Low |

### 2c. UX Features

| # | Item | Impact | Status | Effort |
|---|------|--------|--------|--------|
| U1 | Client-side form validation — pre-submit using field metadata (required, min/max, pattern) | High | ✅ DONE | Low |
| U2 | Bulk edit modal — bulk field-update for selected rows in ListView | High | ✅ DONE | Medium |
| U3 | Inline row editing — click cell to edit in-place for simple fields | High | ✅ DONE | Medium |
| U4 | Atomic batch save — new record + child rows POSTs parent then loops children; partial failure leaves orphan; use `/batch` for atomic parent+children | High | ✅ DONE | Medium |
| U5 | M2M UI — `MultiSelectCombobox` exists but `DynamicForm` only handles child_table (1:M), not bridge-table updates for M2M | High | ✅ DONE | Medium |
| U6 | Soft-delete bin — backend `/deleted` + restore exist; no UI to view or restore archived records | Medium | ✅ DONE | Low |
| U7 | Column visibility storage — currently `localStorage`; persist as `UserPreference` model in backend for multi-device admin | Medium | ✅ DONE | Medium |
| U8 | Dark mode — toggle + store wired ✅; `dark:` Tailwind classes cover only 2 files (95% of UI unaffected) | Medium | ✅ DONE | High |
| U9 | Dashboard drag-to-rearrange — widget reorder exists but uses index-swap only (no splice/move) | Medium | ✅ DONE | Medium |
| U10 | Column resizing & freeze — fixed-width columns; freeze col 1 + drag-to-resize | Medium | ✅ DONE | Medium |
| U11 | Keyboard shortcut map — `?` key shows all shortcuts; `Cmd+K` not wired to CommandPalette | Medium | ✅ DONE | Low |
| U12 | Profile edit — name/email display-only; no edit mode (change-password exists) | Low | ✅ DONE | Low |
| U13 | Inline table ghost rows — "Add Row" pushes blank dict; saving without filling triggers confusing 422 on child fields; validate/discard empty rows before save | Medium | ✅ DONE | Low |
| U14 | Lookup N+1 in InlineChildTable — `InlineLookupCombobox` calls `api.get(target_resource)` per row; 50 rows with same lookup = 50 requests; add React Context cache for lookup dictionaries | High | ✅ DONE | Medium |
| U15 | Metadata-driven tabs — forms with many sections stack vertically; add tab support to `View.layout` so `DynamicForm` renders multi-tab interfaces | Medium | ✅ DONE | Medium |
| U16 | Flexible grid layout — `DynamicForm` hardcoded 2-column grid; add `col_span` to `LayoutSection` field definitions for full-width fields and 3-column grids | Medium | ✅ DONE | Low |
| U17 | Command Palette action search — `Cmd+K` only searches records; add "Action Search" (e.g., "New Invoice", "Go to Settings") for keyboard-driven navigation | Medium | ✅ DONE | Low |
| U18 | Hardcoded field logic in `DynamicForm` — `profile`, `org_id`, `unit_type` handled via `if field.name ===` at lines 634–636; move into metadata system (specialized UI types or choices) | Medium | ✅ DONE | Medium |
| U19 | Form Settings panel — SidePanel-over-ListView approach (no dedicated `/settings/:resource` page); accessible from gear icon in DynamicForm header and "Settings" button in ListView toolbar; supports tabbed layout for Fields/Layout/Columns/Permissions | High | ✅ DONE | Medium |
| U20 | Form Settings tabs — Form Settings page has tabbed layout: **Fields** (label, required, hidden, read-only, default_value, series override per `FieldModel`), **Layout** (drag-and-drop form builder), **List Columns** (column order/visibility), **Permissions** (per-role field visibility) | High | ✅ DONE | High |
| U21 | Drag-and-drop Form Builder — "Layout" tab in Form Settings; drag fields into sections/tabs, reorder sections; persists to `ResourceModel.layout` JSON; `DynamicForm` reads this layout at runtime instead of `View.layout` from code | High | ✅ DONE | High |

### 2d. UI Primitives / Shared Components

| # | Item | Status | Effort |
|---|------|--------|--------|
| P1 | `<Card>` — `bg-white rounded-3xl border border-slate-200 shadow-sm` repeated 37× | ✅ DONE | Low |
| P2 | `<PageShell>` — `animate-in fade-in slide-in-from-bottom-4 duration-500` repeated 10×+ | ✅ DONE | Low |
| P3 | `<LoadingState>` — 4–5 different loading patterns across views; no shared component | ✅ DONE | Low |
| P4 | `<EmptyState>` — inline empty state markup repeated across AppHome, DashboardView, ListView | ✅ DONE | Low |
| P5 | Error notifications — `console.error` in `MainLayout:28`, `HeaderSearch:38`, `Profile:23`, `GlobalSettings:32,71` never reaches `notify()` | ✅ DONE | Low |

### 2e. Repeatables / Tech Debt

| # | Item | Status | Effort |
|---|------|--------|--------|
| R1 | `cleanResourcePath` overuse — manually called in almost every component/hook; abstract into api client or `useResource` hook | ✅ DONE | Low |
| R2 | Service vs. logic location — ERP services (`recalc_mixin.py`, `posting.py`) mixed with models; standardize `services/` folder for all apps | ✅ DONE | Low |
| R3 | Circular import fatigue — local imports inside methods across `model_actions.py`, `model.py`, app actions; introduced `ServiceRegistry` | ✅ DONE | High |
| R4 | `createEmptyRecord` boilerplate — identical `if type==='boolean'`/`date`/`datetime` chains in `DynamicForm.tsx:~262` and `InlineChildTable.tsx:~58`; extract to `SchemaRegistry.createDefaultRecord(metadata)` | ✅ DONE | Low |
| R5 | Hardcoded widget registry — `DashboardView.tsx:87–89` uses `if widget_type==='stat'/'chart'/'list'`; replace with `WidgetRegistry` pattern so app modules inject custom widgets | ✅ DONE | Low |
| R6 | `<SubTableToolbar>` — `InlineChildTable.tsx:78–88` uses full `ListToolbar` with empty stubs (`onExport/onBulkEdit={() => {}}`); needs a dedicated lightweight toolbar | ✅ DONE | Low |

---

## 3. Framework Refactoring

### Phase 1 — Utility Centralization ✅ DONE
Move label formatting (`.replace("_", " ").title()`) from `UIGenerator`, `App`, and `View` into `Aras.helper.to_label_case(name)` in `api/core/lib/helpers.py`. Ensures consistent naming across UI, menus, and breadcrumbs.

### Phase 2 — Modular UIGenerator ✅ DONE
Refactor `UIGenerator.generate_metadata` to a Type Handler Pattern — registry of small handler functions (`_handle_lookup`, `_handle_select`, `_handle_numeric`) replacing the large `if/elif` block. Makes adding new field types (Signature, RichText) safe without touching core.

### Phase 3 — Model & View Enhancements
1. `Aras.Model.get_ui_fields()` — standardize retrieval of non-system visible columns. ✅ DONE
2. Metadata Cache — in-memory dict with flush mechanism in `UIGenerator` to avoid repeated DB queries during high-load UI rendering. ✅ DONE

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

---

## 6. SaaS Product Roadmap

### Fase 0 — FastAPI + React refactor ✅ DONE
- [Gemini] Move core to FastAPI
- [Codex] Move UI to React 19 + Tailwind 4

### Fase 1 — Multi-tenant core ✅ DONE
- [Gemini] Tenant connection router (db-per-tenant)
- [Gemini] Tenant provisioning scripts
- [Gemini] Registry models (AppModel, ResourceModel, etc.)

### Fase 2 — Modul POS ✅ DONE
- [Gemini] PotTerminal, PotSession, PotOrder models
- [Gemini] POS Quick Invoice API
- [Codex] POS UI (Touch friendly)

### Fase 3 — Mobile App (React Native / Expo) ✅ DONE
- [Codex] `mobile/` workspace with App.tsx, screens, navigation, context, locales, store
- [Codex] Resource list/detail screens, LanguageContext (AsyncStorage `aras_lang`)
- ⚠ Known bug: `ResourceListScreen.tsx:28` — fetches `/${resourceName}` directly; nested routes like `stock/items` work, but no scoping/auth header verification done in this review. See qa_frontend.md for mobile follow-ups.

### Fase 4 — Web utama ✅ DONE
- [Gemini] License enforcement middleware
- [Gemini] apps/saas (control plane)
- [Gemini] apps/web (generic CMS)
- [Gemini] Stripe + Midtrans + Xendit pluggable providers + IP geo routing (run 103)

### Fase 5 — Control Plane MVP ✅ DONE
- [Gemini] apps/saas/ with Plan, Subscription, LicenseToken
- [Gemini] Subscription management UI

### Fase 6 — Auto-provisioning ✅ DONE (run 103)
### Fase 7 — Automated billing (APScheduler cron, dunning, overdue) ✅ DONE (run 103)
### Fase 8 — Resource monitoring (request_log middleware + admin KPIs) ✅ DONE (run 103)

---

---

## SaaS Polish & Backend Hardening — Email transport, GeoLite2, Webhook E2E tests (2026-05-29) ✅ DONE
  - [Gemini 2.5 Flash] Pluggable EmailTransport wiring; send_dunning_emails implementation; GeoLite2 auto-fetch script; 7 E2E tests for payment webhooks.

## 7. Audit & QA Findings (docs/qa_backend_{a,b}.md, qa_frontend.md, audit_report_summary_20260525.md)

### Backend QA-A
| Item | Status |
|------|--------|
| Missing `__init__.py` in core packages (base, manager, registry, migrations) | ✅ DONE |
| Duplicate `Note` model (`apps/core/` vs `apps/notes/`) — `apps/core/` removed | ✅ DONE |
| JWT `purpose` claim verified in auth | ✅ DONE (`auth/service.py:86,106`) |
| CRM/Asset/HR/Party/Notes/Dev apps missing `views.py` + autodiscover | ✅ DONE (all 6 views.py present) |
| `installer.py` legacy `__title__` usage | ✅ DONE (no matches) |
| `auto_migrate` orphaned tables (never drops) | ⬜ TODO (intentional — safe default) |
| `router_factory` bare `except:` blocks | ✅ DONE (no matches in core/logic/router_factory/) |
| `discovery.py` ungated `print()` calls | ✅ DONE (module logger replaces print) |

### Backend QA-B
| Item | Status |
|------|--------|
| `report_service._generate_query_report` undefined `script` crash | ✅ DONE (uses `QueryBuilder.execute`, no raw `exec(script)`) |
| Report routers missing `get_current_user` (`/profit-loss`, etc.) | ✅ DONE (`Depends(get_current_user)` present L41,54,68,98) |
| Dev routes missing auth | ✅ DONE (`router-level Depends(require_admin)` L11) |
| Stock `/items/{id}/stock` missing auth | ✅ DONE (`_user=Depends(get_current_user)` L17) |
| Script report `exec()` arbitrary code execution | ✅ DONE (run 102: superuser gate + `script_approved_by_id` + empty `__builtins__` + 5s timeout) |
| `Subscription.approve()` auto-issues license token | ✅ DONE (`LicenseService.issue_license` called L101) |

### Frontend QA-C
| Item | Status |
|------|--------|
| `ListView.tsx` unused `idValue/primaryValue/statusValue` blocking build | ✅ DONE (now used L746,749) |
| `CustomerPortalSetup.tsx` `FormEvent` runtime import | ✅ DONE (`import type` L3) |
| `DynamicForm` missing `display_token` modal | ✅ DONE (`DynamicForm.tsx:90` handles display_token) |
| `CustomerSignup.tsx` silent plan-load failure | ⬜ TODO |
| `PublicLanding.tsx` silent landing fetch failure | ⬜ TODO |
| `CustomerSignup.tsx` discards backend response (no subscription_id) | ⬜ TODO |
| `CustomerPortal.tsx` raw JSON parse (envelope drift) | ⬜ TODO |
| `mobile/ResourceListScreen.tsx:28` resource path replace bug | ✅ DONE (now `api.get('/${resourceName}')` direct, nested paths work) |

### Audit consensus blockers (2026-05-25)
| Item | Status |
|------|--------|
| Tenant/org isolation — `X-Org-ID` validated against user memberships | ✅ DONE (2026-05-26 hardening per aras.md) |
| Unsafe report execution paths | ✅ DONE — query via QueryBuilder; script `exec()` gated by superuser + approval + empty builtins + timeout |
| Startup-time schema mutation in production | ✅ DONE (production startup no longer runs sync per 2026-05-26 framework change) |
| Generic framework regression tests | 🟡 HALF — smoke tests added (BATCH 5 run 100); coverage still thin |
| Mobile/PWA deployment foundations | 🟡 HALF — `mobile/` workspace exists, deploy pipeline not specced |

### Outstanding from audits (not in any current spec)
- `auto_migrate` orphan table drop policy
- `router_factory` bare `except:` cleanup
- `discovery.py` switch `print()` → logger
- Script report `exec()` sandbox/disable
- Public CMS pages silent error swallow (CustomerSignup, PublicLanding, CustomerPortal)
- Mobile deployment + auth header audit

---

## 2026-05-28 — Quality & UX Sweep Plan (Claude Opus 4.7)

### Immediate fixes (this session)

**F-A. Public landing is hardcoded → make it DB-driven + easy edit**
- `LandingSection` model + `/web/landing` endpoint already exist (gemini-flash). PublicLanding.tsx ignores them and uses hardcoded hero/features/testimonials/pricing copy.
- Refactor `ui/src/views/PublicLanding.tsx` to fetch `/web/landing` and render sections by `key` (hero, features, testimonials, cta). Fallback to hardcoded copy only when section missing.
- Section keys recognised: `hero`, `feature.*`, `testimonial.*`, `cta`. Use `body` as JSON for structured sections (feature/testimonial lists) — keep flat `title/subtitle/body/image/cta_*` for hero/cta.
- Template builder extension: register `landing` as a known template in `WebPage.template` choices and surface a "Landing" entry in DevTools → Template Builder. Wire `?from=landing` query so the existing TemplateBuilder loads a landing tree.

**F-B. Login form must follow user's tweak-panel theme**
- Root cause: `MainLayout` applies CSS vars (`--accent`, `--aras-radius`, `--font-scale`, dark class) only when mounted. Login/PublicLanding/Signup routes render *outside* MainLayout → fall back to defaults.
- Lift theme-application effect from `MainLayout` into `App.tsx` (top-level, runs always). Keep the inline `style` on MainLayout for hot-reload, but the persisted theme is now applied at app boot regardless of route.

**F-C. Template Studio doesn't show current page on open**
- Currently `?from=<route>` is only set when launched from `TemplateDesignToggle`. The `DevTools` button at L309 navigates to `/dev/template-builder` with no `from` param → loads default tree.
- Two fixes in `TemplateBuilder.tsx`:
  1. If no `?from=`, read last-known template from `localStorage('template-studio:last')`; persist on every load.
  2. Allow a "current page" picker in `Topbar` that lists known templates (default tree + any saved via `/dev/dev_template_trees` list endpoint).
- Update DevTools launcher to pass `?from=` based on `document.referrer` pathname when available.

### Deferred (multi-session — see `/Users/aras/.claude/plans/check-whole-project-and-expressive-pine.md` for full plan)

- P0 close-out: UserPreference migration, M2M endpoint hardening, metadata cache invalidation hooks, ws listener wiring, column/layout precedence, inline-edit hardening, ActionBar dedup.
- P1 UX: form dirty-state guard, a11y pass, responsive tables, typography/density scale, data-driven CommandPalette, error UX.
- P2 backend quality: split `router_factory.py` (951 LOC) and `model.py` (806 LOC), introduce `Service` base, test scaffolding per app, AI-attribution audit.
- P3 docs: refresh `framework_ref.md` pointers, feature/fix logs, reports.json append.

### Priority 0 — Close in-flight refactor (must ship first)

**B0.1 UserPreference migration & wiring**
- `api/core/auth/models.py` — verify `UserPreference` cols + unique `(user_id, key)`.
- `python manage.py sync` so `auto_migrate` creates table; add to `installer.py` seed.
- `/preference` GET/PUT under JWT, scoped by `user_id` only (never trust client).

**B0.2 M2M endpoint hardening**
- `api/core/logic/router_factory.py` — `PUT /{item_id}/{m2m_field}` `List[int]`:
  - Validate IDs exist + in scope (reject 400, no silent skip — matches 2026-05-26 hardening).
  - Emit `broadcast_sync({event:"m2m_update", resource, id, field})`.

**B0.3 Metadata cache invalidation**
- `api/core/logic/ui_generator.py` — cache key `(resource, lang, org_id)`; invalidate on ResourceModel/FieldModel write (hook RouterFactory post-commit). `/metadata/flush` exists — call from FormSettings save path.

**F0.4 WebSocket listener (dead code now)**
- `ui/src/lib/ws.ts` — connect once in `main.tsx` after auth; reconnect with backoff.
- `ListView.tsx` — listen `aras:record-event` for current resource → refresh row/refetch.
- `DynamicForm.tsx` — on event for current `(resource,id)` show "Record updated externally — reload?" banner.

**F0.5 Column/layout persistence precedence**
- Per-user view state → `UserPreference` key `list:{resource}:columns`.
- Per-resource schema (default columns, layout JSON, hidden) → ResourceModel/FieldModel (admin via FormSettings).
- `FormSettings.tsx` — gate Layout/Permissions behind admin; "List Columns" shows org default + per-user override toggle.

**F0.6 Inline cell edit hardening**
- `ListView.tsx` — type coercion via SchemaRegistry (reuse field renderer in edit mode, not bare `<input>`).
- Lift `validateField()` → `aras-core/lib/validate.ts`; per-cell validation.
- Keyboard: Esc=cancel, Enter=commit+next-row, Tab=commit+next-cell, blur=commit.

**F0.7 ActionBar dedup**
- Delete `ListViewActionBar.tsx` re-export shim; switch imports to `ArasActionBar variant="full"`.
- Export/import/bulk helpers → `lib/listActions.ts`.

### Priority 1 — UI/UX polish

**F1.1 Form dirty-state guard**
- `DynamicForm.tsx` — track `initialValues` vs `values`; expose `isDirty`.
- `MainLayout.tsx` — `useBlocker` on dirty open forms; ConfirmDialog via `useUIStore`.
- Optional autosave for `View.autosave=True`.

**F1.2 Accessibility**
- `ArasTable.tsx` — `role="table"`, `<th scope="col">`, `aria-sort`, arrow-key cell nav.
- `DynamicForm.tsx` — `aria-invalid`, `aria-describedby={errorId}`, focus first invalid on submit.
- `CommandPalette.tsx` — `role="combobox"`, `aria-activedescendant`.
- Restore visible focus rings using `--accent` (Tailwind reset currently suppresses).

**F1.3 Responsive tables**
- `ArasTable.tsx` — below `md` render stacked cards (label:value from visible columns); preserve row-click nav.
- Sticky first column + horizontal-scroll shadow on `sm`.

**F1.4 Typography/density scale**
- `ui/src/index.css` — replace hardcoded `text-[10/12/13px]` with `--fs-xs/sm/base` driven by `--font-scale`.
- Audit ListView, ArasTable, ArasActionBar, Sidebar, Header.

**F1.5 CommandPalette data-driven**
- New `GET /api/v1/admin/quick-actions` aggregating `@Aras.model_action` + recent resources + RBAC-filtered routes.
- `CommandPalette.tsx` — replace hardcoded `ACTIONS`; fuzzy-search server list; cache 60s.

**F1.6 Error UX**
- `aras-core/lib/api.ts` — surface error codes; `useAras().notify({retry: fn})` renders retry chip.
- `DynamicForm.tsx` — pattern errors read `field.info.pattern_hint` not generic message.

**F1.7 Skeleton/empty coherence**
- One shared `<SkeletonRow/>` and `<EmptyState/>` used by ListView, InlineChildTable, ArasTable, DashboardView.

### Priority 2 — Backend quality

**B2.1 Split oversized files**
- `router_factory.py` (951 LOC) → `router_factory/{crud,bulk,m2m,aggregate,search}.py`; keep class facade.
- `base/model.py` (806 LOC) → `model/{queries,hooks,serialization}.py`.

**B2.2 Service base class**
- `api/core/base/service.py` with retrieve/list/create/update/delete + RBAC + audit hooks; refactor accounting/stock/saas to inherit.

**B2.3 Test scaffolding (only 2 test files for 18k LOC)**
- `api/tests/conftest.py` fixtures: `client`, `db`, `admin_user`, `org`.
- Per-app smoke: CRUD on one model, RBAC denial, scope leak, m2m write.

**B2.4 AI attribution audit**
- Grep functions missing `# <model>` tag → backfill `# unknown (needs review)` per CLAUDE.md.

### Priority 3 — Docs

**P3.1** Refresh `docs/framework_ref.md` line pointers after router_factory/model splits; sync pointers in `docs/aras.md`.
**P3.2** Append entries to `docs/feature.md` & `docs/fix.md` for: UserPreference, M2M, metadata cache, FormSettings, ArasTable/ActionBar, ws bridge.
**P3.3** Append `docs/reports.json` per batch (CLAUDE.md rule 5).

### Critical files

**Backend:** `api/core/auth/{models,routes}.py`, `core/logic/router_factory.py` (split+m2m), `core/logic/ui_generator.py` (cache), `core/base/model.py` (split), `core/base/service.py` (new), `core/api/{dev,admin}.py`, `api/main.py`.

**Frontend:** `ui/src/main.tsx`, `lib/ws.ts`, `aras-core/SchemaRegistry.tsx`, `aras-core/components/{ArasActionBar,ArasTable,FormSettings,ListView,InlineChildTable,DynamicForm,CommandPalette}.tsx`, `aras-core/lib/validate.ts` (new), `layouts/MainLayout.tsx`, `store/uiStore.ts`, `index.css`, `components/{SkeletonRow,EmptyState}.tsx`.

**Reuse — do NOT reinvent:** `useAras()`, `MetadataService` cache, `UserPreference`, `broadcast_sync`, `SchemaRegistry.renderField`.

### Verification

**Backend**
1. `cd api && python manage.py sync` — UserPreference table created, no errors.
2. `cd api && pytest -q` — smoke tests green.
3. `PUT /api/v1/<app>/<res>/{id}/<m2m_field>` invalid IDs → 400 (no silent skip).
4. Edit field via FormSettings → next `/metadata` GET reflects without server restart.

**Frontend**
1. `cd ui && npm run typecheck && npm run build` — zero TS errors.
2. Two tabs, edit row in A → B updates via WS within ~1s.
3. Edit form, navigate away → unsaved-changes confirm.
4. Tab through ArasTable header → focus visible, Enter sorts, arrows nav cells.
5. Resize 375px → ListView stacked cards, no overflow.
6. Bad email submit → red outline + screen-reader announces error.
7. Cmd-K → quick actions from `/admin/quick-actions`, RBAC-filtered.

**E2E**
1. Login admin/admin.
2. Create row in `notes` via inline-add.
3. Bulk delete 2 rows → WS broadcast → other tab updates.
4. Switch lang EN/ID → labels translate post-cache-refactor.
