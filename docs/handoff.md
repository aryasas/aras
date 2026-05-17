# Handoff Spec — Payment ↔ Invoice Connection

> run_id: 9
> Written by: Claude Code (claude-sonnet-4-6)
> Date: 2026-05-18
> Feature: Payment ↔ Invoice connection — manual allocation UI and deallocate action

---

## Context
`Payment` and `PaymentAllocation` models exist and `PaymentService` has `allocate`/`deallocate`/`auto_allocate` logic, but there is no way from the UI to link a payment to an invoice. The `allocations` child table on `PaymentView` currently renders raw `invoice_type` and `invoice_id` integer fields — unusable. Goal: wire up manual allocation so a user can pick an invoice, enter amount, and save; and deallocate by deleting a row.

---

## Backend Tasks

UPDATE `api/apps/erp/accounting/models.py`
- On `PaymentAllocation`, add a `@property @Aras.computed_field` named `invoice_number` that reads `invoice_type` and `invoice_id`, fetches the corresponding `InflowInvoice` or `OutflowInvoice` via `object_session(self)`, and returns its `number` string (or `""` if not found).
- On `PaymentAllocation`, add `@Aras.model_action(name="deallocate", permission="edit", label="Remove")` that calls `PaymentService.deallocate(db, self.id)` and returns `ok({"ok": True}, message="Allocation removed.")`.
- On `Payment`, add two `@property @Aras.computed_field` fields: `amount_allocated` = `sum(a.amount for a in self.allocations)` and `amount_unallocated` = `self.amount - self.amount_allocated`.

UPDATE `api/apps/erp/accounting/views.py`
- On `PaymentView`, add a `fields` dict entry for `PaymentAllocation` child fields — specifically `invoice_type` as `{"read_only": True}` and `invoice_id` with `{"ui_type": "async_select", "choices_url": "/api/erp/accounting/payments/{parent_id}/open_invoices", "display_field": "number"}`.
- Add `amount_allocated` and `amount_unallocated` to the `"Payment Details"` tab fields list (after `amount`).
- In `InflowInvoiceView` layout, add tab `{"title": "Payments", "fields": ["amount_paid", "amount_due", "payment_allocations"]}` — these computed fields already exist on the model.
- In `OutflowInvoiceView` layout, add the same `"Payments"` tab.

UPDATE `api/apps/erp/accounting/app.py`
- Add a custom route `GET /payments/{payment_id}/open_invoices` under the accounting router. Load the `Payment` by `payment_id`, determine invoice model from `payment_type` (Incoming → InflowInvoice, Outgoing → OutflowInvoice), call `PaymentService.get_unpaid_invoices(db, payment.party_type, payment.party_id, payment.org_id)`, return list of `{id, number, total_amount, amount_due, doc_date}` dicts. Use `amount_due` computed field — it's already defined on both invoice models.

---

## Frontend Tasks

No custom component needed if the framework's child table renders `async_select` for `invoice_id`. Verify:

- `Allocations` tab on Payment form: invoice picker dropdown (populated from `open_invoices` endpoint), editable amount field, "Remove" row action from `deallocate` model action.
- `Payment Details` tab: `amount_allocated` and `amount_unallocated` render as read-only computed fields.
- `InflowInvoice` form `Payments` tab: shows `amount_paid`, `amount_due`, and read-only `payment_allocations` child table with `invoice_number`, `amount` columns.
- `OutflowInvoice` form same.

If `async_select` is not supported by the framework's child table renderer, add a minimal frontend workaround: in the allocation row edit, fetch `GET /api/erp/accounting/payments/{parentId}/open_invoices` and render a `<select>` for `invoice_id`.

---
<!-- ── Below this line is filled automatically by multi_agent.py + Claude ── -->

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


---
## Agent Reports (revision (2026-05-18))

### Backend (Gemini 2.5 Flash)
- files_written: api/apps/erp/accounting/models.py, api/apps/erp/accounting/views.py, api/apps/erp/accounting/app.py
- features_added: Added payment-invoice connection functionality including computed fields, model actions, view configurations, and a new API endpoint for open invoices.
- fixes_applied: none
- framework_changes: none
- issues: none

### Frontend (Codex GPT-5.5)
- files_written: ui/src/aras-core/components/InlineChildTable.tsx, ui/src/aras-core/components/DynamicForm.tsx
- features_added: Added child-table async invoice selection for payment allocations and deallocate-backed remove action
- fixes_applied: Payment allocation rows now infer read-only invoice_type from parent payment_type
- framework_changes: none
- issues: none

## Claude Review
- verdict: APPROVED (with direct fixes applied)
- reviewed_by: Claude Code (claude-sonnet-4-6)
- date: 2026-05-18
- notes: Fixed 3 bugs before approving — (1) models.py import changed from `..base` to `.base` (wrong), reverted; (2) app.py used nonexistent `supplier_id` attribute on Payment, replaced with `party_id` throughout; (3) top-level `PaymentService` import in app.py caused ImportError on startup due to unrelated missing models in the service file — moved to lazy imports inside the route handler. Sync passes clean.
