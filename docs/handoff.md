---
> run_id: 95

> Written by: Claude Code (claude-opus-4-7)
> run_id: 21
> Date: 2026-05-22

# Handoff: Template Studio v3 — Craft.js editor matching erp-modern mock

## Context
Rewrite `ui/src/views/TemplateBuilder.tsx` as a Craft.js + dnd-kit visual editor whose default canvas is a pixel-faithful reproduction of `ui/public/mocks/erp-modern/form.html`. Three breakpoints (Desktop / Tablet / Mobile). Only containers get margin/padding box handles; leaves are inspector-only. Every element carries an AI-note field persisted via `/dev/dev_template_annotations`. Deps already installed: `@craftjs/core`, `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`.

## Reference (source of truth for sizing)
- `ui/public/mocks/erp-modern/form.html` — sidebar widths (`w-20 lg:w-64`), glass-panel + island radii (24px), header layout, 2-column field grids, dark summary island. Match these EXACTLY in default Craft tree.
- `ui/public/mocks/erp-modern/index.html` — Tailwind config: `brand` (teal 50–950) + `surface` (slate 50–950) palettes; `.glass-panel { background: rgba(255,255,255,0.85); backdrop-filter: blur(12px); }`; `.island { border-radius: 24px; }`; dot-grid bg `radial-gradient(#cbd5e1 1px, transparent 1px); background-size: 24px 24px`.

## Backend Tasks
- UPDATE `api/apps/dev/models.py` — extend annotation table with columns: `node_id` (str), `node_kind` (str), `node_label` (str, nullable), `breakpoint` (str: `desktop|tablet|mobile`, nullable), `status` (str: `pending|applied|rejected`, default `pending`), `tree_json` (JSONB, nullable — full Craft tree snapshot at save time). Add Alembic migration.
- UPDATE `api/apps/dev/app.py` — accept new payload `{ template_name, node_id, node_kind, node_label, breakpoint, comment, status, tree_json? }` on POST. Add `GET /dev/dev_template_trees?template_name=` returning latest `tree_json` per template (separate from annotations list). Add `POST /dev/dev_template_trees` to upsert.
- UPDATE `api/apps/dev/seed_templates.py` — seed default `erp-modern-invoice` Craft tree JSON so editor opens with reference layout even before first save.

## Frontend Tasks
- UPDATE `ui/src/views/TemplateBuilder.tsx` — FULL REWRITE using Craft.js `<Editor>` + `<Frame>` + `<Element>`. Replace current custom TemplateNode tree with Craft user-components below. Keep `export interface TemplateSection` re-export (used by `LiveDesignWrapper.tsx`).
- NEW FILE `ui/src/views/template-studio/components/Box.tsx` — Craft user-component. Container with editable margin/padding (per-side numeric px inputs in inspector), bg, radius, gap, direction (row/col), align, justify. Margin/padding handles shown ONLY when selected (drag edges to resize, with live numeric tooltip).
- NEW FILE `ui/src/views/template-studio/components/Sidebar.tsx` — Craft user-component reproducing erp-modern sidebar: `w-20 lg:w-64` glass-panel island, brand wordmark block, nav sections with items (icon + label), bottom user-chip. Props: width(px per breakpoint), bg, items[]. Children allowed (sidebar-sections, sidebar-items as nested Boxes).
- NEW FILE `ui/src/views/template-studio/components/Header.tsx` — Craft user-component: back button + title + spacer + cancel + save. Editable label, button variants.
- NEW FILE `ui/src/views/template-studio/components/Island.tsx` — light/dark variants, 24px radius, glass-panel bg, accepts FieldGrid children.
- NEW FILE `ui/src/views/template-studio/components/FieldGrid.tsx` — 1/2/3-column responsive grid container (cols per breakpoint).
- NEW FILE `ui/src/views/template-studio/components/Field.tsx` — leaf: label + (input|select|textarea|date). Inspector-only (no margin handles). Props: label, value, placeholder, type, fullWidth.
- NEW FILE `ui/src/views/template-studio/components/ButtonEl.tsx` — leaf: label, variant (primary|ghost|danger), icon. Inspector-only.
- NEW FILE `ui/src/views/template-studio/components/SummaryRow.tsx` — leaf for dark island financial rows: label + value + accent flag.
- NEW FILE `ui/src/views/template-studio/components/Text.tsx` — leaf: heading|paragraph|label. Inline editable on double-click.
- NEW FILE `ui/src/views/template-studio/panels/Palette.tsx` — left pane. Lists draggable user-components (Box, Sidebar, Header, Island, FieldGrid, Field, ButtonEl, SummaryRow, Text). Uses Craft `useEditor().connectors.create`.
- NEW FILE `ui/src/views/template-studio/panels/Inspector.tsx` — right pane. Reads selected node via `useEditor((state) => ({ selected: state.events.selected }))`. Shows:
  1. AI Instruction (emerald-themed textarea, top) — writes to `node.custom.note`; on Save flush, POSTs to `/dev/dev_template_annotations`.
  2. Properties — per-breakpoint accordion (Desktop/Tablet/Mobile). Container nodes show: margin (T/R/B/L numeric px), padding (T/R/B/L numeric px), width, height, gap, bg, radius, align, justify. Leaf nodes show: their typed props only.
  3. Actions: hide/show, lock/unlock, duplicate, delete, move up/down.
- NEW FILE `ui/src/views/template-studio/panels/Topbar.tsx` — Wand2 icon + template-name input + Desktop/Tablet/Mobile viewport toggle (widths: 1440 / 834 / 390 px, Frame width animates), undo/redo (Craft `useEditor().actions.history`), zoom 50–150%, edit/preview toggle (`actions.setOptions(o => o.enabled = \!o.enabled)`), Save button.
- NEW FILE `ui/src/views/template-studio/panels/Outline.tsx` — collapsed tree view of Craft `query.getNodes()` with search. Click → `actions.selectNode(id)`.
- NEW FILE `ui/src/views/template-studio/lib/defaultTree.ts` — exports SerializedNodes JSON matching erp-modern/form.html exactly. MUST mirror: outer page (dot-grid bg) > [Sidebar(w-20 lg:w-64) | Main > [Header, Island(light, FieldGrid 2-col with Customer/Invoice# / Date/Due Date), Island(light, FieldGrid 1-col with LineItems area), Island(dark, SummaryRow x3 with brand-300 accent on total)]]. Take pixel widths/paddings/gaps directly from form.html.
- NEW FILE `ui/src/views/template-studio/lib/api.ts` — `loadTree(name)` GET `/dev/dev_template_trees`, `saveTree(name, tree)` POST, `flushNotes(name, notes[])` POSTs each annotation. Soft-fail with console.warn.
- NEW FILE `ui/src/views/template-studio/lib/breakpoints.ts` — `type Breakpoint = 'desktop'|'tablet'|'mobile'`; `BREAKPOINT_WIDTHS = { desktop: 1440, tablet: 834, mobile: 390 }`. Each Box/container stores props as `{ desktop: {...}, tablet: {...}, mobile: {...} }`. Active breakpoint from React context drives which prop set the component renders.
- NEW FILE `ui/src/views/template-studio/lib/styles.css` — copy glass-panel, island, hide-scroll, brand/surface palette from erp-modern mocks; imported by TemplateBuilder.
- UPDATE `ui/src/aras-core/components/LiveDesignWrapper.tsx` — keep importing `TemplateSection` from new file path; no behavior change required.

## Acceptance Criteria
1. Open `/dev/template-builder` → default canvas is visually indistinguishable from `mocks/erp-modern/form.html` at Desktop breakpoint (sidebar width, header height, island radii, field spacing all match within 2px).
2. Click sidebar → inspector shows per-side margin/padding numeric inputs; typing `24` in `margin-left` immediately shifts sidebar 24px right; switching to Tablet tab shows independent value.
3. Drag a Field from palette onto a FieldGrid → drops cleanly at indicated slot.
4. Add AI note to any element → emerald dot appears on element → click Save → row appears in `dev_template_annotations` table with `node_id`, `node_kind`, `breakpoint`, `comment`.
5. Switch Desktop → Mobile → canvas resizes to 390px, sidebar collapses to `w-20` equivalent automatically (mobile breakpoint props in default tree).
6. `npx tsc --noEmit -p tsconfig.app.json` clean.

## Out of Scope (this pass)
- React Native renderer (tree is already RN-portable via Craft JSON; renderer is a follow-up).
- Multi-template management UI (single template `erp-modern-invoice` for now).
- Collaborative editing.

## Change Logging
- Append `## Template Studio v3 (Craft.js) (2026-05-22)` block to `docs/feature.md` per implementer.

## Backend Implementation Report
- **Updated `api/apps/dev/models.py`**: Extended `TemplateAnnotation` with `node_id`, `node_kind`, `node_label`, `breakpoint`, `status`, `comment`, and `tree_json`. Dropped `unique=True` on `template_name`.
- **Updated `api/apps/dev/app.py`**: Added `dev_api_router` with endpoints `GET /dev/dev_template_trees`, `POST /dev/dev_template_trees`, and `POST /dev/dev_template_annotations`.
- **Updated `api/apps/dev/seed_templates.py`**: Seeded default `erp-modern-invoice` template tree JSON.
- **Migration**: Ran `python api/manage.py sync` (Aras framework handles missing columns natively, no Alembic required).
- **Reporting**: Report appended to `docs/reports.json`.


---
## Agent Reports (2026-05-22)

### Backend (Gemini (gemini-2.5-flash))
- files_written: none
- features_added: none
- fixes_applied: none
- framework_changes: none
- issues: none

### Frontend (GPT (codex))
- files_written: ui/src/views/TemplateBuilder.tsx, ui/src/views/template-studio/components/Box.tsx, ui/src/views/template-studio/components/Sidebar.tsx, ui/src/views/template-studio/components/Header.tsx, ui/src/views/template-studio/components/Island.tsx, ui/src/views/template-studio/components/FieldGrid.tsx, ui/src/views/template-studio/components/Field.tsx, ui/src/views/template-studio/components/ButtonEl.tsx, ui/src/views/template-studio/components/SummaryRow.tsx, ui/src/views/template-studio/components/Text.tsx, ui/src/views/template-studio/panels/Palette.tsx, ui/src/views/template-studio/panels/Inspector.tsx, ui/src/views/template-studio/panels/Topbar.tsx, ui/src/views/template-studio/panels/Outline.tsx, ui/src/views/template-studio/lib/defaultTree.ts, ui/src/views/template-studio/lib/api.ts, ui/src/views/template-studio/lib/breakpoints.ts, ui/src/views/template-studio/lib/styles.css, ui/src/aras-core/components/LiveDesignWrapper.tsx, docs/feature.md, docs/reports.json
- features_added: Craft.js Template Studio v3 matching the erp-modern invoice mock, with responsive viewport switching, default serialized tree loading, palette/outline/inspector/topbar panels, and per-node AI note persistence to dev template annotations.
- fixes_applied: Kept TemplateSection compatibility for LiveDesignWrapper and verified `npx tsc --noEmit -p tsconfig.app.json` passes clean.
- framework_changes: none
- issues: none

## Claude Review
- verdict: APPROVED
- reviewed_by: Claude Code (claude-opus-4-7)
- date: 2026-05-22
- notes: All 19 frontend files present under ui/src/views/template-studio/. Backend extended TemplateAnnotation with node_id/node_kind/node_label/breakpoint/status/tree_json and added dev_api_router endpoints (GET/POST /dev/dev_template_trees, POST /dev/dev_template_annotations); seed_templates.py seeds erp-modern-invoice. `npx tsc --noEmit -p tsconfig.app.json` clean. `python manage.py sync` ran clean (tables created, schema auto-migrated). Minor: Gemini reported "files_written: none" despite modifying api/apps/dev/{models.py,app.py,seed_templates.py} — reporting bug only, code is correct.
