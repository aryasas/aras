# Handoff Spec

> Written by: Claude Code (claude-opus-4-8)
> Date: 2026-06-08
> Feature: Make DevTools a first-class framework module — surface its 16 tools through the standard menu system (sidebar app + TopMenuBar) and DELETE its bespoke in-page tab strip. One navigation system, fully framework-native (Option B).

---

## Context & Problem

On `/admin/dev` two horizontal navigation systems stack:
1. The framework's `TopMenuBar` (app module strip, driven by the active app's `menu_groups`).
2. DevTools' OWN bespoke 16-tab strip rendered inside `ui/src/views/DevTools.tsx`.

This is a double menu. The fix (Option B, user-chosen): DevTools stops shipping its own tab strip and instead exposes its 16 tools as normal menu entries through the framework's existing menu mechanism. After this change, navigating DevTools uses the SAME `TopMenuBar` every other app uses; each tool is its own route.

**Key enabling fact (already verified — DO NOT add new framework plumbing):**
`api/core/base/app.py` menu builder ALREADY supports custom links inside `menu_groups`:
```python
# Custom links: {"label": "...", "path": "...", "icon": "..."}
for link in group.get("links", []):
    group_items.append({"type": "link", "name": ..., "label": ..., "path": link["path"], "icon": ...})
```
So DevTools' tools are expressed as `links` in `menu_groups` — ZERO backend framework changes needed. The frontend `TopMenuBar` already renders `type: "link"` items as navigation to their `path`.

---

## The 16 DevTools tools (current tab → component → target route)

Current tabs live in `ui/src/views/DevTools.tsx` `tabs[]` (lines ~128-145). Each maps to a render block or component:

| Tool | Component (in `ui/src/views/devtools/` unless noted) | New route | Icon |
|------|------|------|------|
| Overview | inline block in DevTools.tsx (+ `<SystemTab/>`, `<TenantSwitcher/>`) → extract to `views/devtools/OverviewTab.tsx` | `/admin/dev` (index) | LayoutDashboard |
| Workbench | inline block in DevTools.tsx (WorkflowCards) → extract to `views/devtools/WorkbenchTab.tsx` | `/admin/dev/workbench` | Wrench |
| Schema | `SchemaTab` | `/admin/dev/schema` | GitCompare |
| Timeline | `RequestTimeline` | `/admin/dev/timeline` | Activity |
| Routes | `RouteDebugger` | `/admin/dev/routes-debug` | Route |
| Models | `ModelRegistry` | `/admin/dev/models` | Boxes |
| Cache | `CacheControl` | `/admin/dev/cache` | Trash2 |
| Commands | `DevCommandPalette` | `/admin/dev/commands` | Command |
| Test Lab | `ApiConsole` | `/admin/dev/test-lab` | Zap |
| SQL Runner | `SqlRunner` | `/admin/dev/sql` | Terminal |
| Access | `AccessTab` | `/admin/dev/access` | Shield |
| Handoff | inline block in DevTools.tsx (handoff runs table + drawer) → extract to `views/devtools/HandoffTab.tsx` | `/admin/dev/handoff` | GitBranch |
| Mocks | `MockGallery` (currently defined INSIDE DevTools.tsx) → extract to `views/devtools/MockGallery.tsx` | `/admin/dev/mocks` | Globe |
| API Help | inline block in DevTools.tsx → extract to `views/devtools/ApiHelpTab.tsx` | `/admin/dev/api-help` | Code2 |
| Scaffold | `ScaffoldTab` | `/admin/dev/scaffold` | Code2 |
| Logs | `LogStream` | `/admin/dev/logs` | AlertTriangle |

> NOTE on route naming: existing `App.tsx` ALREADY has `dev/routes`, `dev/health`, `dev/tasks`, `dev/template-builder`, `dev/help`, `dev/activity-heatmap`, `dev/handoff-runs`, and catch-alls `dev/:resource` + `dev/table/...`. To avoid collisions, use the NEW paths in the table above (e.g. `routes-debug`, `test-lab`). The catch-all `dev/:resource` MUST be declared AFTER all explicit dev tool routes or it will swallow them.

---

## Backend Tasks (Gemini)

### 1. Give the dev app real `menu_groups` of links
UPDATE `api/apps/dev/app.py` (the `DevToolsApp` class).
- Keep `hide_from_sidebar` ABSENT/False (DevTools must appear in the sidebar icon rail as a normal app).
- Keep `have_home = True` (so clicking the app navigates to its home `/admin/dev`).
- Add a `menu_groups` class attribute grouping the 16 tools as **links** (NOT models). Group them logically:
  ```python
  menu_groups = [
      {"label": "Inspect", "icon": "Search", "links": [
          {"name": "dev_overview", "label": "Overview", "path": "/admin/dev", "icon": "LayoutDashboard"},
          {"name": "dev_schema", "label": "Schema", "path": "/admin/dev/schema", "icon": "GitCompare"},
          {"name": "dev_models", "label": "Models", "path": "/admin/dev/models", "icon": "Boxes"},
          {"name": "dev_routes", "label": "Routes", "path": "/admin/dev/routes-debug", "icon": "Route"},
          {"name": "dev_timeline", "label": "Timeline", "path": "/admin/dev/timeline", "icon": "Activity"},
      ]},
      {"label": "Operate", "icon": "Wrench", "links": [
          {"name": "dev_workbench", "label": "Workbench", "path": "/admin/dev/workbench", "icon": "Wrench"},
          {"name": "dev_cache", "label": "Cache", "path": "/admin/dev/cache", "icon": "Trash2"},
          {"name": "dev_commands", "label": "Commands", "path": "/admin/dev/commands", "icon": "Command"},
          {"name": "dev_sql", "label": "SQL Runner", "path": "/admin/dev/sql", "icon": "Terminal"},
          {"name": "dev_access", "label": "Access", "path": "/admin/dev/access", "icon": "Shield"},
      ]},
      {"label": "Build & Test", "icon": "Code", "links": [
          {"name": "dev_testlab", "label": "Test Lab", "path": "/admin/dev/test-lab", "icon": "Zap"},
          {"name": "dev_scaffold", "label": "Scaffold", "path": "/admin/dev/scaffold", "icon": "Code2"},
          {"name": "dev_mocks", "label": "Mocks", "path": "/admin/dev/mocks", "icon": "Globe"},
          {"name": "dev_apihelp", "label": "API Help", "path": "/admin/dev/api-help", "icon": "Code2"},
          {"name": "dev_handoff", "label": "Handoff", "path": "/admin/dev/handoff", "icon": "GitBranch"},
          {"name": "dev_logs", "label": "Logs", "path": "/admin/dev/logs", "icon": "AlertTriangle"},
      ]},
  ]
  ```
  (Exact grouping/labels above are the target; keep all 16 tools.)
- The dev app's `models = [...]` list (Aras.AppModel etc.) must NOT appear as standalone menu items cluttering the strip. The menu builder auto-appends visible models not in any group into a "General" group. To suppress that, the dev app's framework/registry models are introspection models, not CRUD destinations — verify they are already non-visible in the menu (check `_view_label`/visible_models logic in `api/core/base/app.py`); if they DO leak into the menu, the cleanest fix is to ensure those models are marked hidden from menu (e.g. `__hidden__`/menu-exclude flag the framework already honors — confirm the attribute name in `app.py` before using; do NOT invent a new one). Report what you found.

### 2. Sync so the manifest persists
- After editing, the menu_groups land in the DB-backed app manifest via the registry sync engine on `python manage.py sync` (run by the user). No migration needed. Confirm `get_manifest()` emits the new `menu_groups`.

### 3. Verify
- `cd api && python manage.py sync` (user runs) → dev app manifest carries the 3 groups, 16 links.
- The `/app-menu/dev` (or equivalent menu endpoint the frontend calls — see `ui/src/layouts/hooks/useAppMenu.ts`, it requests `normalizeRoutePath(activeApp.path||/dev).replace(/^\//,'')`) returns the grouped link menu.

---

## Frontend Tasks (Codex)

### 1. Extract each DevTools tab body into its own routed view
The bespoke tab strip in `ui/src/views/DevTools.tsx` is being DELETED. Each tool becomes a standalone view rendered by a route.
- Tools already backed by a standalone component (`SchemaTab`, `RequestTimeline`, `RouteDebugger`, `ModelRegistry`, `CacheControl`, `DevCommandPalette`, `ApiConsole`, `SqlRunner`, `AccessTab`, `LogStream`, `ScaffoldTab`) — just route to them directly.
- Tools currently inline inside DevTools.tsx — EXTRACT into new files under `ui/src/views/devtools/`:
  - `OverviewTab.tsx` — the overview block (stat strip, quick actions, tenant switcher, framework info, `<SystemTab/>`, registries, DB stats). Move the overview-only helper components it uses (`StatCell`, `ActionChip`, `InfoRow`, `RegistryCard`, and the data fetch for `info`/`stats`) with it.
  - `WorkbenchTab.tsx` — the workbench WorkflowCards block (and `WorkflowCard`, `InspectButton`, `MiniMetric` helpers if only used here).
  - `HandoffTab.tsx` — handoff runs table + detail drawer + `fetchHandoffRuns`.
  - `MockGallery.tsx` — move the `MockGallery`/`MockCard`/`MOCK_ENTRIES` currently defined inside DevTools.tsx into this file; export default.
  - `ApiHelpTab.tsx` — the API Help block (Swagger links + endpoint list).
- Each extracted view is self-contained (does its own data fetching). Preserve all current behavior, styling (design tokens — `var(--surface)` etc.), and the `MockGallery` live-preview design just built.

### 2. Replace the DevTools shell
`ui/src/views/DevTools.tsx` becomes a THIN layout/index:
- DELETE the `tabs[]` array, the tab strip render (the `filteredTabs.map(...)` button bar), the `activeTab` state, the `?tab=` syncing, and all the `{activeTab === '...' && ...}` blocks.
- KEEP a slim DevTools header if useful (title + global Sync button + `<DevHealthPanel/>`), OR drop the header entirely and let each routed view stand alone — choose the cleaner result; the module strip (`TopMenuBar`) now provides tool navigation.
- DevTools.tsx (route `/admin/dev`) should render the Overview view as the index.

### 3. Register routes in `ui/src/App.tsx`
Add explicit routes (lazy-imported) for every tool, placed BEFORE the existing catch-all `dev/:resource` routes (lines ~260-261) so they aren't swallowed:
```tsx
<Route path="dev" element={<DevToolsView />} />            {/* index = Overview */}
<Route path="dev/workbench" element={<WorkbenchTab />} />
<Route path="dev/schema" element={<SchemaTab />} />
<Route path="dev/timeline" element={<RequestTimeline />} />
<Route path="dev/routes-debug" element={<RouteDebugger />} />
<Route path="dev/models" element={<ModelRegistry />} />
<Route path="dev/cache" element={<CacheControl />} />
<Route path="dev/commands" element={<DevCommandPalette />} />
<Route path="dev/test-lab" element={<ApiConsole />} />
<Route path="dev/sql" element={<SqlRunner />} />
<Route path="dev/access" element={<AccessTab />} />
<Route path="dev/handoff" element={<HandoffTab />} />
<Route path="dev/mocks" element={<MockGallery />} />
<Route path="dev/api-help" element={<ApiHelpTab />} />
<Route path="dev/scaffold" element={<ScaffoldTab />} />
<Route path="dev/logs" element={<LogStream />} />
{/* existing dev/template-builder, dev/health, dev/tasks, dev/help, dev/activity-heatmap, dev/handoff-runs stay */}
{/* the catch-all dev/:resource and dev/table/* MUST remain AFTER all of the above */}
```
Ensure the existing `dev/routes` (InspectRoutesView) and the new `dev/routes-debug` (RouteDebugger) don't conflict — they are different tools; keep both.

### 4. Update internal navigation
- Anywhere in the codebase that did `setActiveTab('handoff')`, `?tab=...`, or navigated within DevTools via tab state must now use the new routes (e.g. `navigate('/admin/dev/handoff')`). Grep `setActiveTab`, `?tab=`, and `activeTab` usages outside DevTools.tsx (e.g. `DevHealthPanel.tsx`, `DevCommandPalette.tsx`) and repoint them.
- The DevCommandPalette tool entries that jump to tabs must navigate to routes instead.

### 5. Verify
- `cd ui && npx tsc --noEmit` → clean.
- `/admin/dev` shows the module strip (3 groups, 16 links) from `TopMenuBar`, NO second bespoke tab strip, and renders Overview.
- Each link routes to the correct tool view.

---

## Invariants (must hold)
- NO new framework menu plumbing — reuse the existing `menu_groups[].links` mechanism in `api/core/base/app.py`.
- DevTools has exactly ONE navigation system after this change (the framework `TopMenuBar`); the bespoke `tabs[]` strip is gone.
- All 16 tools remain reachable; no tool lost.
- `dev/:resource` catch-all stays LAST among dev routes.
- Design tokens preserved; the new MockGallery preview UI preserved.
- Frontend `tsc --noEmit` clean; backend `manage.py sync` emits the new menu.

---
<!-- ── Below this line is filled automatically by multi_agent.py + Claude ── -->
