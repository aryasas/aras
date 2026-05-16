 Now fixed

  - pytest -q: 20 passed.
  - npm run build: passes, and the large single-bundle warning is gone.
  - Route lazy loading/code splitting is in place.
  - Bootstrap seed logic moved out to api/core/manager/bootstrap.py.
  - PATCH now uses PatchSchema, not raw dict.
  - ListView bulk delete now uses cleanResourcePath(resource).
  - Login page no longer has the Default credentials: admin / admin match.
  - Input-schema “not yet implemented” message is gone.
  - No untracked test_relations.db in git status, though the file still exists locally.

  Still remaining / note

  - tests/test_via_requests.py still contains stale /auth/login and /query/sys_settings, but it is excluded by
    tests/conftest.py.
  - Admin user is still auto-created in bootstrap if missing. It uses env password, but creation itself is still
    automatic.
  - Local DB files still exist: test_relations.db, api/aras.db.
  - Worktree has many modified files and new files, so review before committing:
      - Modified includes .gitignore, api/main.py, router/UI/test files, ui/vite.config.ts.
      - New includes api/core/manager/bootstrap.py, pytest.ini, tests/conftest.py.


## Change Logging Rule + Manual Log Command (2026-05-14)
  - [Claude Code] _parse_claude_review now wired via --submit-review flag


## Dashboard Drag-to-Rearrange + Audit Log Timeline View — revision (2026-05-14)
  - [Codex/GPT-5.5] Added drag state reset and error notification for failed layout save


## App Navigation Restructure — have_home + Topbar App Menu — revision (2026-05-14)
  - [Codex/GPT-5.5] Removed expandable SidebarAppMenu usage for app entries


## App Navigation Restructure — have_home + Topbar App Menu (2026-05-14)
  - [Claude Code] Suppress urllib3 NotOpenSSLWarning in multi_agent.py via warnings.filterwarnings before requests import


## App Navigation Restructure — have_home + Topbar App Menu (2026-05-14)
  - [Claude Code] Suppress urllib3 NotOpenSSLWarning; fix IndentationError in main.py (if __name__ block)

## ERP App Structure Consolidation (2026-05-15)
- [Gemini CLI] Fixed mistake where ERP modules were split into separate apps. Consolidated `erp_config`, `erp_stock`, `erp_accounting`, `erp_crm`, `erp_supplier`, and `erp_pos` into a single unified `erp` application in `api/apps/erp/`.
- [Gemini CLI] Restructured ERP models into sub-packages (`erp/config`, `erp/stock`, etc.) within the single ERP app.

## Child List View Not Showing on Parent Form (2026-05-15)
- [Claude Sonnet 4.6] Fixed `sync_manager.py` bug where `_child_map` entries (dicts) were passed as strings to DB query — caused crash during `manage.py sync`.
- [Claude Sonnet 4.6] Fixed corrupt JSON columns in DB (empty string instead of `[]`/`{}`) via `tools/fix_db_json.py`.
- [Claude Sonnet 4.6] Fixed `ui_generator.py`: `fk_column` now included in `child_table` field info (both DB and code-fallback paths).
- [Claude Sonnet 4.6] Fixed `DynamicForm.tsx`: child list `fixedFilters` now uses `field.fk_column` (e.g. `invoice_id`) instead of generic `{resource}_id` which was wrong.


## Date picker not opening in DynamicForm (2026-05-15)
- [Claude Sonnet 4.6] Fixed `SchemaRegistry.tsx`: replaced `disabled` prop with `readOnly` on DateInput/DateTimeInput so the native date picker is never suppressed; removed global `outline-none` in favour of `focus:outline-none`; added `cursor-pointer` and `disabled:opacity-50` utility classes.

## Child Table Always Shows "Save the Record First" on Edit (2026-05-15)
- [Claude Sonnet 4.6] Fixed `DynamicForm.tsx`: replaced `id && id !== 'new'` condition with `currentId != null` state. Introduced `currentId` state initialized from `id` prop; synced via a `useEffect([id])`; updated after POST save so child tables appear immediately after creating a new record without navigation. All child table filters, FK initialData, workflow/action URLs now use `currentId`.


## InlineChildTable — extract to own file, fix double-wrap, clean toolbar — revision (2026-05-15)
  - [Codex/GPT-5.5] removed child table double-wrap and filtered child tables out of layout section grids

## Fix: Topbar Dropdown Clipping (2026-05-15)
- [Gemini CLI] **CSS Overflow Context**: Removed `overflow-x-auto` and `scrollbar-hide` from the topbar container in `TopbarAppMenu.tsx`. These classes were creating a formatting context that clipped absolute-positioned child elements (dropdown menus), preventing sub-menus from rendering visibly on the screen. Changed to `flex-wrap` with `min-h-[44px]` to support wrapping on smaller screens while retaining dropdown visibility.


## Replace scope system with Company-aware RBAC (Expanded RBAC) — revision (2026-05-15)
  - [Codex/GPT-5.5] logout now clears active company storage


## Purchase/Sales Invoice Stock Movement + Journal Integration (2026-05-16)
  - [Claude Sonnet 4.6] JournalEntry/PurchaseInvoice/SalesInvoice/StockMovement missing currency_id and total_tax fields; JournalService wrong kwarg; CoaResolver wrong account_type filter values


## Workflow Engine (DB-driven) + FK Label Fix + Child Table Fix + Series Sub-module + Field Customization Fix + App Manager Sub-module Fix — revision (2026-05-16)
  - [Codex/GPT-5.5] Child table FK loading/saving uses fk_column fallback correctly; field customization header shows parent resource context

## Fix: Child Table Data Not Loading in DynamicForm (2026-05-16)
- [Claude Sonnet 4.6] api/core/logic/ui_generator.py — added `resolve_api_path()` helper and `api_path`/`target_api_path` fields to metadata response; child_table fields now include correct hierarchical REST paths
- [Claude Sonnet 4.6] ui/src/aras-core/components/DynamicForm.tsx — use `metadata.api_path` for resource CRUD calls; use `f.target_api_path` for child resource fetch; send `filters` as JSON instead of raw query param
- [Claude Sonnet 4.6] ui/src/aras-core/components/InlineChildTable.tsx — removed duplicate data fetch (DynamicForm is now sole data owner for child rows)


## Fase 0 Closeout + Fase 1 Foundation (Multi-Tenant Core) — revision (2026-05-16)
  - [Codex/GPT-5.5] Global API response envelope handling for {success,data,message,error}


## ARP Neutral Rename — Organization model, neutral DB schema, profile system, POT rename, party consolidation — revision (2026-05-16)
  - [Codex/GPT-5.5] replaced visible Company text with Organization and removed Supplier navigation entries from generated menus


## Purchase Flow (GRN, AP matching) + Reporting (Trial Balance, P&L, AR/AP Aging) — revision (2026-05-16)
  - [Codex/GPT-5.5] <!-- filled by agent -->


## CMP Phase — DRY refactor + UX gaps + error normalization — revision (2026-05-16)
  - [Gemini] Corrected import path in print_router.py.


## ERP Form Layouts, UI Bugs, Report Center Filters, HandoffRun DB Tracking — revision (2026-05-16)
  - [Codex/GPT-5.5] styled DynamicForm metadata error card; report loading skeleton while generating

## TypeScript Build: 22 Errors Fixed (2026-05-17)
- [Claude Sonnet 4.6] `ui/src/aras-core/hooks/useAras.ts` — added `appName` (first URL segment via `useLocation`) to returned object
- [Claude Sonnet 4.6] `ui/src/lib/api.ts` — added `detail?: string | null` to `ApiEnvelope` interface
- [Claude Sonnet 4.6] `ui/src/aras-core/components/DynamicForm.tsx` — added `app_name?` to `Metadata` interface; fixed `handleSubmit` used-before-declaration via `handleSubmitRef`; removed unused `totalSkeletons` and renamed unused `f` params to `_f` in skeleton map callbacks; added `useRef` import
- [Claude Sonnet 4.6] `ui/src/aras-core/components/ListView.tsx` — fixed `dataPath` undefined in `handleExport` (replaced with `cleanResource`); removed `fetchSavedFilters` from metadata useEffect deps (declared later); updated `ImportMapping` call to new API (`csvData`, `onImport`, full `ResourceField` shape); replaced `executeImport` with `executeImportData` using `/import-bulk`
- [Claude Sonnet 4.6] `ui/src/aras-core/components/InlineChildTable.tsx` — added missing `ListToolbar` props: `onSaveFilter`, `onApplySavedFilter`, `onDeleteSavedFilter`, `savedFilters`
- [Claude Sonnet 4.6] `ui/src/aras-core/components/ImportMapping.tsx` — removed unused `useAras` import and `notify` destructure
- [Claude Sonnet 4.6] `ui/src/aras-core/components/NotificationHistory.tsx` — removed unused `X` import
- [Claude Sonnet 4.6] `docs/aras.md` + `docs/framework_ref.md` — updated `useAras()` hook documentation to reflect full return shape


## none (2026-05-17)
  - [Claude Sonnet 4.6] Fixed _get_clean_path stripping only parent prefix instead of full parent+app prefix for nested sub-apps (e.g. erp_hr_employees → /erp/hr/hr-employees instead of /erp/hr/employees), causing 404 on metadata endpoint for HR, Party, and other double-prefixed modules
