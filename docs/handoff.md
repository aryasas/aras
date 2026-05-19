> Written by: Claude Code (claude-sonnet-4-6)
> Date: 2026-05-19
> Feature: LinkedDoc auto-discovery, Payment fixes, POS view, Generic form tabs

---

## Context

Four features in one run:
1. **LinkedDoc auto-discovery** — instead of manual `__linked_docs__` declarations, scan SA mapper FKs automatically (port from `aras-old/arasCore/lib/services/linked_doc_detector.py`). `__linked_docs__` becomes an escape hatch only for polymorphic (type+id) relationships.
2. **Payment fixes** — `party_id` on Payment must be a real FK → Combobox. Add "Get Invoices" and "Auto Allocate" action buttons to the PaymentAllocation child table header.
3. **POS view** — custom POS screen. Each transaction creates an Invoice directly (no PotOrder). Inflow mode = purchase invoices, Outflow mode = sales invoices. Shift report = aggregates computed from linked invoices, not stored separately.
4. **Generic linked_list tab** — new layout section type `"type": "linked_list"` that renders a filtered embedded ListView inside a form tab.

---

## Backend Tasks

### B1: LinkedDoc auto-discovery
UPDATE `api/core/base/model.py` — replace `get_linked_documents(db)` and `_cascade_linked_docs(db)` with two-pass logic:

**Pass 1 — SA FK auto-scan** (no declaration needed):
```python
from sqlalchemy import inspect as sa_inspect
SKIP_COLS = {"created_by", "updated_by", "org_id", "deleted_at", "created_at", "updated_at"}
mapper_registry = sa_inspect(type(self)).mapper.registry
target_table = self.__tablename__
for m in mapper_registry.mappers:
    child_cls = m.class_
    if child_cls is type(self) or not hasattr(child_cls, "__tablename__"):
        continue
    for col in m.persist_selectable.columns:
        if col.name in SKIP_COLS:
            continue
        for fk in col.foreign_keys:
            if fk.column.table.name == target_table:
                # found a child that FKs to self
                children = db.query(child_cls).filter(
                    getattr(child_cls, col.key) == self.id
                ).all()
                # resolve resource URL via App._registry (use _resolve_table from linked_doc.py)
                # yield each child as {label, resource, id, number}
```
Only yield models that have `__tablename__` (skip abstract). For cascade: call `child.delete_self(db)` if `getattr(child, "deleted_at", None) is None`, else `db.delete(child)`.

**Pass 2 — explicit `__linked_docs__`** (unchanged): walk `self.__class__.__linked_docs__` as before.

UPDATE `api/core/base/linked_doc.py` — keep the class but remove caching fields (`_resolved_model` etc.) since auto-resolution is now in model.py. Keep `LinkedDoc(table, filters, condition, cascade, show)` for the explicit pass.

UPDATE `api/apps/erp/accounting/models.py`:
- `InflowInvoice.__linked_docs__` — remove `PaymentAllocation` entry (auto-discovered via `invoice_id` FK). Keep `JournalEntry` and `StockMovement` (polymorphic).
- `OutflowInvoice.__linked_docs__` — same.

UPDATE `api/apps/erp/stock/models.py`:
- `StockMovement.__linked_docs__` — remove `StockMovementLine` entry (auto-discovered via `movement_id` FK).

---

### B2: Payment fixes
UPDATE `api/apps/erp/accounting/models.py`:

`Payment.party_id` — change from `mapped_column(Integer, nullable=True)` to:
```python
party_id: Mapped[Optional[int]] = mapped_column(
    ForeignKey("erp_party_parties.id"), nullable=True,
    info={"ui_type": "lookup", "target_resource": "erp/party/parties", "display_column": "name"}
)
```

Add model action on `Payment` that returns open invoices as pre-fill data for the allocation table:
```python
@Aras.model_action(name="get_open_invoices", permission="edit", label="Get Invoices")
def get_open_invoices(self, db):
    from .services.payment import PaymentService
    rows = PaymentService.get_unpaid_invoices(db, self)
    # Return in a format the frontend can use to prefill allocations child table
    prefill = [{"invoice_type": r["invoice_type"], "invoice_id": r["id"], "amount": r["amount_due"]} for r in rows]
    return ok({"prefill_field": "allocations", "rows": prefill}, message="Open invoices loaded.")
```

UPDATE `api/apps/erp/accounting/views.py` — `PaymentView`: change the allocations section to include action buttons:
```python
{"title": "Allocations", "fields": ["amount_allocated", "amount_unallocated", "allocations"], "actions": ["get_open_invoices", "auto_allocate"]}
```

---

### B3: POS backend
UPDATE `api/apps/erp/accounting/models.py` — add `pos_session_id` to both invoice models:
```python
# on InflowInvoice and OutflowInvoice:
pos_session_id: Mapped[Optional[int]] = mapped_column(
    ForeignKey("erp_pot_sessions.id"), nullable=True, info={"hidden": True}
)
```

UPDATE `api/apps/erp/pot/models.py`:
- Add `mode` field to `PotSession`: `Mapped[str]` with `info={"choices": ["sales", "purchase"]}`, default `"sales"`.
- Remove the `orders` relationship reference (keep table, just remove relationship for now).
- Add computed fields to `PotSession`:
  - `total_sales` → sum of `OutflowInvoice.total_amount` where `pos_session_id = self.id`
  - `total_purchase` → sum of `InflowInvoice.total_amount` where `pos_session_id = self.id`
  - `invoice_count` → count of linked invoices
  - `payment_summary` → list `[{mode_name, total_amount}]` from payments on linked invoices
- Model action `close_session(db, data)` — sets `closing_balance = data.get("closing_balance", 0)`, sets `status = "Posted"`. No PotOrder creation.

NEW FILE `api/apps/erp/pot/routers.py` — add two endpoints mounted on the pot app router:

`GET /pot/sessions/{session_id}/items` — returns items filtered by session mode:
- mode=sales → `Item.for_sales == True`
- mode=purchase → `Item.for_purchase == True`
- Include `id, code, name, default_sale_price` (or `default_purchase_price`), `qty_on_hand`
- Must use `org_id` from JWT scope

`POST /pot/sessions/{session_id}/quick_invoice` — body: `{party_id?, items: [{item_id, qty, unit_price}], payment_mode_id, amount_paid}`:
1. Determine invoice type from session mode: `sales` → `OutflowInvoice`, `purchase` → `InflowInvoice`
2. Create Invoice with lines, set `pos_session_id = session_id`, set `org_id` from session
3. Call `post_stock_movement` and `post_journal_entry` handlers (reuse existing workflow)
4. Create `Payment` and `PaymentAllocation` for `amount_paid` (up to invoice total)
5. Return `{invoice_number, invoice_id, change_amount}`

UPDATE `api/apps/erp/pot/app.py` — register the new router.

---

### B4: linked_list tab — no backend change needed
The layout JSON `type: "linked_list"` is already returned as-is from `UIGenerator` since it passes unknown layout types through. No backend change required.

UPDATE `api/apps/erp/pot/views.py` — add `linked_list` to PotSessionView layout:
```python
layout = [
    {"key": "header", "title": "Header", "fields": ["number", "terminal_id", "mode", "status", "doc_date", "opening_balance", "closing_balance"]},
    {"key": "summary", "title": "Summary", "fields": ["total_sales", "total_purchase", "invoice_count"]},
    {"type": "linked_list", "title": "Sales Invoices", "resource": "erp/accounting/outflow-invoices", "fk_field": "pos_session_id"},
    {"type": "linked_list", "title": "Purchase Invoices", "resource": "erp/accounting/inflow-invoices", "fk_field": "pos_session_id"},
]
```

---

## Frontend Tasks

### F1: linked_list tab rendering — UPDATE `ui/src/aras-core/components/DynamicForm.tsx`

In the layout map loop (around line 1251 where `'tabs' in entry` is checked), add a new case for `entry.type === 'linked_list'`. Render it as a card panel containing a `<ListView>` with:
- `resource={entry.resource}`
- `fixedFilters={{ [entry.fk_field]: currentId }}`  
- `onRowClick={(id) => navigate('/' + entry.resource + '/' + id)}`
- No `onAdd` prop (read-only list)
- Only render when `currentId \!= null`

This is reusing the existing ListView component — minimal code. Import ListView (already imported). Wrap in same card styling as other sections.

---

### F2: Payment — prefill allocations from action result — UPDATE `ui/src/aras-core/components/DynamicForm.tsx`

In `handleModelAction` (the function that calls model actions), after receiving the action response, check if `result.data.prefill_field` exists. If so, find the matching child table field and merge `result.data.rows` into `childRows[prefill_field]`, overwriting existing rows. The `get_open_invoices` action returns `{prefill_field: "allocations", rows: [...]}` — this pre-populates the allocation table so the user can review/edit before saving.

---

### F3: POS View — NEW FILE `ui/src/views/PosView.tsx`

Standalone POS screen. Route: detect at `erp/pot/sessions/:id/pos` in `App.tsx` (add route before the `segment1/*` catch-all).

**Structure:**
```
┌──────────────────────────────────────────────────────────┐
│ [←] Session #POS-001  [SALES badge]  [Close Session btn]  │
├──────────────────────────┬───────────────────────────────┤
│  [Search items...]       │  Cart                         │
│                          │  ─────────────────────────── │
│  ┌──────┐ ┌──────┐       │  Item A    qty [-][2][+]  100 │
│  │Item A│ │Item B│       │  Item B    qty [-][1][+]   50 │
│  │ 50k  │ │ 30k  │       │  ─────────────────────────── │
│  └──────┘ └──────┘       │  Subtotal:             150    │
│  ┌──────┐ ┌──────┐       │                               │
│  │Item C│ │Item D│       │  Party: [Combobox...........]  │
│  │ 20k  │ │ 15k  │       │  Mode:  [Combobox...........]  │
│  └──────┘ └──────┘       │  Paid:  [____________]        │
│                          │  Change: 0                    │
│                          │  [     CHARGE     ]           │
└──────────────────────────┴───────────────────────────────┘
```

- Fetch items from `GET /erp/pot/sessions/{id}/items`
- Charge button: POST to `/erp/pot/sessions/{id}/quick_invoice`, on success show a brief toast with invoice number + change amount, then clear cart
- Close Session: calls `close_session` model action, redirects to `/erp/pot/sessions`
- Items panel: 3-column grid, each card shows name + price. Click adds to cart (qty=1, clicking again increments)
- Cart qty: inline +/- buttons, 0 removes item
- Payment mode: Combobox sourced from `erp/config/payment-modes`
- Party: optional Combobox sourced from `erp/party/parties`

Use Tailwind classes consistent with the rest of the app. No custom CSS.

Register route in `ui/src/App.tsx`:
```tsx
<Route path="erp/pot/sessions/:id/pos" element={<PosView />} />
```
Add lazy import at top of App.tsx.

---

#---

## Agent Report (Gemini 2.5 Flash)
- files_written: api/core/base/model.py, api/core/base/linked_doc.py, api/apps/erp/accounting/models.py, api/apps/erp/stock/models.py, api/apps/erp/accounting/views.py, api/apps/erp/pot/models.py, api/apps/erp/pot/routers.py, api/apps/erp/pot/app.py, api/apps/erp/pot/views.py
- features_added: LinkedDoc auto-discovery (Pass 1: SA FK scan), Payment.get_open_invoices pre-fill action, POS backend (sessions, quick_invoice, shift summary), linked_list layout support in views.
- fixes_applied: Payment.party_id FK correction and metadata.
- framework_changes: Refactored Model for auto-discovery; added App.get_routers for custom endpoints.
- issues: none.
- verdict: APPROVED


---
## Agent Reports (2026-05-19)

### Backend (Gemini 2.5 Flash)
- files_written: none
- features_added: none
- fixes_applied: none
- framework_changes: none
- issues: none

### Frontend (Codex GPT-5.5)
- files_written: ui/src/aras-core/components/DynamicForm.tsx, ui/src/views/PosView.tsx, ui/src/App.tsx
- features_added: linked_list form tab rendering, model action allocation prefill handling, POS session view and route
- fixes_applied: none
- framework_changes: none
- issues: Backend close_session action may not accept payload through the generated action route as currently implemented

## Claude Review
- verdict: APPROVED
- reviewed_by: Claude Sonnet 4.6
- date: 2026-05-19
- notes: All files verified. `close_session` had a signature mismatch (no `input_schema` → router called `handler(db)` but method expected `data: dict`). Fixed directly in `api/apps/erp/pot/models.py` — added `_CloseSessionInput(PydanticBaseModel)` inner class and wired `input_schema=_CloseSessionInput` to the decorator. DB sync needs to be run manually (`cd api && python manage.py sync`) — DB unreachable in review sandbox.
