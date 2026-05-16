# Handoff Spec

> Written by: Claude Code (claude-sonnet-4-6)
> Date: 2026-05-16
> Feature: Phase 2 UX — Keyboard Shortcuts, Dashboard Drill-down, Print/PDF, Import Validation

---

## Context
Four UX improvements: global keyboard shortcuts (Ctrl+S to save, Escape to cancel), stat widget click-through to filtered list, print/PDF preview for documents, and import row validation preview before posting.

---

## Backend Tasks

NEW FILE `api/apps/erp/accounting/routers/print_router.py`
- GET `/api/v1/accounting/{resource}/{id}/print` — returns a JSON payload with all fields needed to render a printable document view (header fields + lines + charges + org info)
- Resource can be: `erp_accounting_inflow_invoices`, `erp_accounting_outflow_invoices`, `erp_accounting_grns`, `erp_accounting_delivery_notes`
- Fetch the record + its lines + org name from Config → Organization (org_id)
- Return flat dict: `{ doc_type, doc_number, date, party_name, lines: [...], charges: [...], subtotal, total_charge, total_amount, org_name }`
- Register router in `api/apps/erp/accounting/app.py` with prefix `/accounting`

---

## Frontend Tasks

UPDATE `ui/src/aras-core/components/DynamicForm.tsx` — Keyboard shortcuts
- Add `useEffect` that listens for `keydown` on `document`:
  - `Ctrl+S` (or `Cmd+S` on Mac): call `handleSubmit()`, prevent default
  - `Escape`: call `onCancel()` if prop exists
- Remove listener on unmount

UPDATE `ui/src/aras-core/components/DashboardView.tsx` — Stat widget drill-down
- Import `useNavigate` from react-router-dom
- In `StatWidget`: wrap the whole card `div` in a `button` (or add `onClick`)
- On click: `navigate(`/${widget.resource_name}`)` — navigates to the ListView for that resource
- Add `title="Click to view all records"` and `cursor-pointer` class

UPDATE `ui/src/aras-core/components/DashboardView.tsx` — List widget row click
- In `ListWidget` rows: add `onClick={() => navigate(`/${widget.resource_name}/${item.id}`)}` with `cursor-pointer hover:bg-slate-50` 

NEW FILE `ui/src/aras-core/components/PrintPreview.tsx`
- Modal overlay component that fetches `/api/v1/accounting/{resource}/{id}/print` and renders a clean printable layout:
  - Header: org name (top-left), doc_type + doc_number (top-right), date + party_name below
  - Lines table: description, qty, unit_price, subtotal columns
  - Footer: subtotal, charges, total_amount
  - Two buttons: "Print" (`window.print()`) and "Close"
  - Use `@media print` via inline `<style>` to hide buttons and set margins on print
- Props: `resource: string`, `id: number | string`, `onClose: () => void`

UPDATE `ui/src/aras-core/components/DynamicForm.tsx` — Print button
- If `metadata.app_name` is `erp_accounting` and record has an `id` (edit mode), show a "Print" button (Printer icon) in the form action bar
- Clicking it: renders `<PrintPreview resource={resource} id={id} onClose={...} />` as an overlay

UPDATE `ui/src/aras-core/components/ImportMapping.tsx` — Validation preview
- After user maps columns and before calling the import API, add a "Validate" step:
  - Parse the CSV rows client-side using the mapping
  - Check required fields are non-empty, numeric fields are valid numbers
  - Show a preview table: rows with errors highlighted in red, valid rows in green
  - Show count: "X valid, Y errors"
  - Two buttons: "Fix & Re-upload" (resets) and "Import Anyway" (proceeds skipping invalid rows) and "Import All" (posts everything)

---
<!-- ── Below this line is filled automatically by multi_agent.py + Claude ── -->

## Agent Reports (2026-05-16)

### Backend (Gemini 2.5 Flash)
- files_written: <!-- filled by agent -->
- features_added: <!-- filled by agent -->
- fixes_applied: <!-- filled by agent -->
- framework_changes: <!-- filled by agent -->
- issues: <!-- filled by agent -->

### Frontend (Gemini 2.5 Flash)
- files_written: <!-- filled by agent -->
- features_added: <!-- filled by agent -->
- fixes_applied: <!-- filled by agent -->
- framework_changes: <!-- filled by agent -->
- issues: <!-- filled by agent -->

## Claude Review
- verdict: APPROVED (with Claude fix)
- reviewed_by: Claude Code
- date: 2026-05-16
- notes: Gemini's print_router.py used non-existent AppManager.get_model_class and wrong ArasModel import — Claude rewrote it with direct model imports (InflowInvoice, OutflowInvoice, GoodsReceiptNote) and proper Party/Organization DB lookups. All other files verified: DynamicForm keyboard shortcuts (Ctrl+S, Escape) confirmed; DashboardView StatWidget + ListWidget drill-down navigate confirmed; PrintPreview modal with print CSS confirmed; ImportMapping validation preview step confirmed.
