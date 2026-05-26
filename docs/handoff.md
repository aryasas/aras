> Written by: Claude Code (claude-sonnet-4-6)
> run_id: 99
> Date: 2026-05-26
> Feature: Framework remaining items — all NOT DONE and HALF from plan.md verified against actual codebase

---

# Handoff: All Remaining Items (Code-Verified)

## Context
Aras is a FastAPI + React 19 framework. Backend: `api/`, Frontend: `ui/src/`. Core: `api/core/`. Apps: `api/apps/`. UI core: `ui/src/aras-core/components/`. Views: `ui/src/views/`.

Verified via codebase audit 2026-05-26. Only items confirmed NOT DONE or HALF in actual code are listed.

---

## Priority: HIGH

### H3: Type FieldProps in SchemaRegistry.tsx
**FILE** `ui/src/aras-core/SchemaRegistry.tsx` lines 23–29
- `value`, `onChange`, `field`, `formData` still loosely typed (union types, not proper interfaces)
- Type `value` as `unknown`, `onChange` as `(val: unknown) => void`, `field` as `FieldDefinition`, `formData` as `Record<string, unknown>`
- Fixes 102 downstream `any` uses

### U1: Client-side form validation
**FILE** `ui/src/aras-core/components/DynamicForm.tsx`
- No validation logic before submit — `required`, `min_length`, `max_length`, `pattern` from field metadata unused on client
- Add pre-submit loop: iterate fields, check constraints, show inline error below each field, block submit if any fail

### U5: M2M UI in DynamicForm
**FILE** `ui/src/aras-core/components/DynamicForm.tsx`
- `field_type === 'm2m'` not handled — only `child_table` (1:M) works
- Add: `if field.field_type === 'm2m'` → render `MultiSelectCombobox`
- On save: `PUT /{resource}/{id}/{field_name}` with `{ ids: [...] }`
- Backend `api/core/base/router.py`: add `PUT /{id}/{m2m_field}` route calling `model.set_m2m(field, ids, db)`

### U14: Fix lookup cache in InlineChildTable (HALF)
**FILE** `ui/src/aras-core/components/InlineChildTable.tsx` lines 21–26
- `lookupCache` Map declared but never populated or read — cache is dead code
- Wire it: before `api.get(target_resource)`, check cache; on response, populate cache
- Result: 50 rows with same FK = 1 request instead of 50

### R3: Circular imports — ServiceRegistry
**FILE** new `api/core/service_registry.py`
- Local imports inside methods across `model_actions.py`, `model.py`, app actions
- Create `ServiceRegistry = {}` dict; register services at startup; replace local imports with `ServiceRegistry.get('name')`
- First: `grep -rn "from api.apps" api/core/` to find which app imports are inside core methods

### U19 + U20 + U21: Form Settings Panel + Tabs + Drag-Drop Builder
**FILES** `ui/src/aras-core/components/DynamicForm.tsx` + new `ui/src/aras-core/components/FormSettings.tsx`
- No FormSettings component exists at all
- Add gear icon to DynamicForm header → opens SidePanel
- SidePanel tabs: **Fields** (label/required/hidden/read-only/default per FieldModel), **Layout** (drag-drop builder), **List Columns** (order/visibility), **Permissions** (per-role field visibility)
- Layout tab: drag fields into sections/tabs; save to `ResourceModel.layout` via `PUT /resource_model/{id}`
- DynamicForm reads `ResourceModel.layout` at runtime; falls back to `View.layout` if null
- Add "Settings" button to ListView toolbar → same SidePanel

---

## Priority: MEDIUM

### U3: Inline row editing
**FILE** `ui/src/aras-core/components/ListView.tsx`
- Table cells are read-only — no click-to-edit
- Click cell → render input (type from schema); Tab/Enter → `PATCH /{resource}/{id}` single field; Esc cancels

### U7: Column visibility → backend UserPreference
**FILE** `ui/src/aras-core/components/ListView.tsx` line 88
- `useState` only — no persistence at all (not even localStorage)
- Save: `PUT /user_preference` with `{ key: 'columns:{resource}', value: JSON.stringify(cols) }`
- Load: `GET /user_preference?key=columns:{resource}`, fallback to default

### U10: Column resizing & freeze
**FILE** `ui/src/aras-core/components/ListView.tsx`
- Header sticky exists but no column freeze or resize
- Freeze col 1: `position: sticky; left: 0; z-index: 1` on first `<td>`/`<th>`
- Resize: add drag handle on `<th>` right border, mousedown/mousemove updates col width state

### U16: col_span in DynamicForm
**FILE** `ui/src/aras-core/components/DynamicForm.tsx`
- Hardcoded 2-column grid, no `col_span` support — not in codebase at all
- Read `col_span` from field definition (default 1); apply `gridColumn: span ${col_span}`

### U18: Remove hardcoded field logic (VERIFIED DONE — skip)
- Audit confirmed: no hardcoded `if field.name ===` in DynamicForm. Already metadata-driven.

### U8: Dark mode — complete Tailwind coverage
**FILES** all `ui/src/` files
- 0 files have `dark:` classes — toggle exists but entire UI has no dark styling
- Run `grep -rL "dark:" ui/src/aras-core/components/ ui/src/views/` to enumerate all files
- Add `dark:` variants for bg, text, border in all components systematically

### WS: WebSocket — wire to actual events
**FILE** find `/ws` endpoint — `grep -rn "websocket\|/ws" api/`
- Stub only; not broadcasting anything
- After any POST/PATCH/DELETE: broadcast `{ event: 'record_updated', resource, id }` to connected clients
- Frontend: create `ui/src/lib/ws.ts` — connect on app load, dispatch context actions on message

---

## Priority: LOW

### U12: Profile edit mode
**FILE** `ui/src/views/Profile.tsx`
- Name/email display-only; password change exists but no account edit
- Add Edit button → fields become inputs → Save calls `PATCH /user/me`

### U17: Command Palette action search
**FILE** `ui/src/aras-core/components/CommandPalette.tsx`
- Only searches records (`/search?q=`)
- Add static actions list: `{ label: 'New Invoice', action: () => navigate('/accounting/invoice/new') }`
- Show in results alongside records

### B16: Global search — fix `__title__` stale ref
**FILE** `api/core/logic/query.py` line 97
- `__title__` attribute no longer exists on models
- Replace with View registry lookup for `title_field`; build searchable index at startup

### B17: ResourceRegistry — centralized FK map
**FILE** `api/core/logic/ui_generator.py`
- Full app registry scan per FK request
- Build `FK_RESOURCE_MAP = { ModelClass: '/path' }` once at startup in `api/core/registry.py`

### B18: Icons — replace PrimeIcons with Lucide
**FILES** `api/apps/accounting/views.py`, `api/apps/asset/views.py`, `api/apps/party/views.py`, `api/apps/config/views.py`
- `grep -rn "pi pi-" api/apps/` → replace each with Lucide name equivalent

### B19: Seed framework
**FILES** `api/apps/*/seed_*.py`
- Seeding scattered; each app needs `App.seed(db)` method
- `manage.py seed` calls `app.seed(db)` per registered app

---

## Section 3: Framework Refactoring (all phases TODO)

### Phase 1 — Utility Centralization
**FILE** new `api/core/lib/helpers.py`
- `.replace("_", " ").title()` repeated in `UIGenerator`, `App`, `View`
- Extract to `Aras.helper.to_label_case(name)`

### Phase 2 — Modular UIGenerator
**FILE** `api/core/logic/ui_generator.py`
- Large `if/elif` block for field types
- Refactor to handler registry: `{ 'lookup': _handle_lookup, 'select': _handle_select, 'numeric': _handle_numeric }`

### Phase 3 — Model & View Enhancements
- `Aras.Model.get_ui_fields()` — standardize retrieval of non-system visible columns
- Metadata Cache — in-memory dict with flush in `UIGenerator` to avoid repeated DB queries

### Phase 4 — Developer Experience
- `GET /api/v1/dev/metadata/flush` endpoint to clear metadata cache without restart

---

## Verification

```bash
cd api && python manage.py sync
cd ui && npm run build
```

---

## Agent Reports (DATE)

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
<!-- Format same as Backend/Frontend Tasks above -->
<!-- Delete this section if APPROVED -->
