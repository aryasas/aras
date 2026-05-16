You have to input your plan here. No delete. Add plan, mark done which done.

# GUI Redesign Plan For Admin Operators by Codex GPT 5.5

  ## Summary

  Redesign the ui/ app around dense, reliable admin workflows: faster scanning, clearer actions, better responsive behavior, and less decorative visual weight. Keep the
  React/Vite structure and existing backend APIs intact.

  ## Key Changes

  - Establish shared UI primitives for buttons, inputs, cards, page headers, empty states, status badges, dialogs, and side panels; replace repeated Tailwind one-offs with
    consistent sizing, focus states, and rounded-lg/rounded-xl instead of rounded-3xl/rounded-[2.5rem].
  - Rework the app shell: make the sidebar responsive, auto-expand the active app section, add collapsed-state tooltips for all icon-only controls, tighten header height/
    padding, and make global search usable on narrow screens.
  - Redesign CRUD list views for admin density: compact toolbar, persistent bulk-action bar, clearer filter builder, robust empty/loading/error states, better pagination copy
    for zero records, accessible column picker, row keyboard/focus support, and horizontal table behavior that does not break mobile.
  - Redesign dynamic forms: quieter sticky action bar, clearer section hierarchy, consistent field spacing, better validation placement, accessible required/read-only states,
    and less visual nesting for child tables.
  - Clean up dashboard/settings/dev pages: replace marketing-style cards and decorative blobs with operational panels, tighter grids, clear primary actions, and status-
    oriented summaries.
  - Improve overlays: make dialogs and side panels keyboard dismissible, focus-trapped, labeled for screen readers, and visually consistent with the redesigned controls.
  - Fix obvious UX bugs found during inspection: global search route fallback, inactive Configure/delete app card buttons, icon-only buttons without labels, and inconsistent
    alert usage versus the app dialog system.

  ## Interfaces

  - No backend API changes.
  - No metadata schema changes.
  - Add internal reusable UI components under the frontend component layer, with props for variant, size, loading, disabled, icon, and accessible labels where relevant.
  - Keep existing route structure and dynamic metadata-driven list/form behavior.

  ## Test Plan

  - Run npm run build and npm run lint in ui/.
  - Manually verify core routes: /, /settings, /apps, /dev, /settings/rbac, dynamic list routes, dynamic edit/new routes, login, dialogs, and side panels.
  - Check desktop, tablet, and mobile widths for sidebar, header search, tables, forms, modals, and child table sections.
  - Verify keyboard behavior: tab order, Escape closes overlays/dropdowns, Enter/Space activate controls, focus remains visible.
  - Verify admin workflows: search, filters, sort, pagination, column toggles, bulk delete confirmation, import/export, form save/cancel, action dialogs, and child record
    creation.

  ## Assumptions

  - Optimize for admin operators, not marketing or first-time onboarding.
  - Preserve current app architecture, data flow, and API contracts.
  - Favor compact, utilitarian UI over decorative cards, large radii, hover-only affordances, and oversized page sections.


  ARAS Framework — Improvement Recommendations
    
    SISTEM (Backend)
  
    ┌─────┬─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┬────────┬────────┐
    │  #  │                                                                                          Item                                                                                           │ Impact │ Effort │
    ├─────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────┼────────┤
    │ 1   │ Batch API endpoint — /batch for bulk create/update/delete. RouterFactory generates single-record only.                                                                                  │ High   │ Medium │
    ├─────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────┼────────┤
    │ 2   │ Field-level validation rules in metadata — Declarative min, max, regex, custom on Field(). Router validates before hitting DB. Currently only DB constraints catch errors.              │ High   │ Medium │
    ├─────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────┼────────┤
    │ 3   │ Pre/post model hooks (signal system) — @Aras.on_create, @Aras.on_update signals on model. Audit manager uses SQLAlchemy events internally but there's no user-facing hook API.          │ High   │ Medium │
    ├─────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────┼────────┤
    │ 4   │ Soft delete routing integration — __soft_delete__ flag exists on model but RouterFactory doesn't generate DELETE → restore or filter out soft-deleted records automatically in queries. │ Medium │ Low    │
    ├─────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────┼────────┤
    │ 5   │ WebSocket endpoint — Real-time push for audit logs, workflow state changes, dashboard refresh. Currently all React Query polling.                                                       │ Medium │ High   │
    ├─────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────┼────────┤
    │ 6   │ Rate limiting + request throttling — No middleware for protecting endpoints from abuse. Critical for multi-tenant or public deployments.                                                │ High   │ Low    │
    └─────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┴────────┴────────┘
  
    ---
    UI (Frontend)
  
    ┌─────┬─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┬────────┬────────┐
    │  #  │                                                                                    Item                                                                                     │ Impact │ Effort │
    ├─────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────┼────────┤
    │ 1   │ Bulk Edit modal — ListView has bulk delete, missing bulk field-update for selected rows.                                                                                    │ High   │ Medium │
    ├─────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────┼────────┤
    │ 2   │ Inline row editing — Click cell to edit in-place in ListView (for simple fields). Currently must open full form.                                                            │ High   │ Medium │
    ├─────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────┼────────┤
    │ 3   │ Form field validation rules rendered — DynamicForm has errors state and displays them, but no client-side pre-validation before submit (required, min/max length, pattern). │ High   │ Low    │
    ├─────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────┼────────┤
    │ 4   │ Column resizing & freeze — ListView columns are fixed-width. Freeze first column + drag-to-resize for wide tables.                                                          │ Medium │ Medium │
    ├─────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────┼────────┤
    │ 5   │ Keyboard shortcut map — CMD+K palette exists but no discoverable shortcut reference. Add ? key to show all shortcuts.                                                       │ Medium │ Low    │
    ├─────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────┼────────┤
    │ 6   │ Dark mode — Tailwind's dark: classes ready, but no toggle exists. Missing uiStore dark preference + <html> class toggle.                                                    │ Medium │ Low    │
    ├─────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────┼────────┤
    │ 7   │ Dashboard drag-to-rearrange — Widget layout exists per user, but no drag-and-drop reordering UI. Static layout only.                                                        │ Medium │ High   │
    ├─────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼────────┼────────┤
    │ 8   │ Audit log timeline view — AuditLogs.tsx is only 21 lines (stub). Full timeline with diff viewer (before/after field values) is missing.                                     │ High   │ Low    │
    └─────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┴────────┴────────┘
  
    ---
    Priority Pick (highest ROI)
    
    Sistem: Rate limiting (low effort, high security), soft delete routing (flag already exists), field validation rules (declarative, clean).
  
    UI: Audit log timeline (21-line stub → real feature), client-side form validation, dark mode toggle (Tailwind already supports it).
  
    Want to start on any of these?
