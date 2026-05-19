> Written by: Claude Code (claude-sonnet-4-6)
> Date: 2026-05-19
> Feature: POS fixes + Tenant Admin UI

---

## Context

Fase 1 (multi-tenant core) is fully implemented — `core/tenant/router.py`, `registry.py`, `provisioner.py`, and `/api/v1/tenants` API all exist. Fase 2 (POS) has two backend bugs blocking the shift report, plus two missing pieces for SaaS readiness: tenant management admin page and POS receipt modal.

---

## Backend Tasks

### B1: Fix PotService stale imports + SQLAlchemy 2.0 compat
UPDATE `api/apps/erp/pot/services/pot.py` — the file currently has two import blocks at the top. The first block (lines 1–6) imports non-existent names `PosSession, PosOrder, PosOrderLine, PosPaymentLine, PosTerminal` (old naming). Remove the first block entirely. Keep only the second import block. Then replace all deprecated `db.query(X).get(id)` calls with `db.get(X, id)` throughout the file — affects `get_pot_products`, `process_order`, `open_session`, `close_session`, `get_shift_report`.

Also fix `get_shift_report` — it calls `session.orders` but that relationship is commented out on PotSession (line 30 of models.py). Replace with an explicit query:
```python
orders = db.query(PotOrder).filter(PotOrder.session_id == session_id).all()
```
Use this `orders` list instead of `session.orders` everywhere in `get_shift_report`. `order.payments` is fine — that relationship is defined on `PotOrder`.

### B2: Restore PotSession.orders relationship
UPDATE `api/apps/erp/pot/models.py` — uncomment line 30:
```python
orders: Mapped[list["PotOrder"]] = relationship("PotOrder", back_populates="session", cascade="all, delete-orphan")
```
Also add `back_populates="session"` to `PotOrder.session` (currently missing it):
```python
session: Mapped["PotSession"] = relationship("PotSession", back_populates="orders")
```

---

## Frontend Tasks

### F1: Tenant Admin page
NEW FILE `ui/src/views/TenantAdmin.tsx` — admin-only page mounted at `/admin/tenants`.

**Section 1 — Provision New Tenant** (card):
- Form: `tenant_id` (text input, required, slug hint), `db_name` (text input, optional, placeholder `aras_tenant_{tenant_id}`)
- "Provision" button → POST `/api/v1/tenants/provision` → on success notify + refresh list; on error show inline error message

**Section 2 — Active Tenants** (table):
Columns: Tenant ID | DB Name | Actions
- Fetch GET `/api/v1/tenants` → `data.data[]`
- Row actions: "Seed" → POST `/api/v1/tenants/{id}/seed` with `window.confirm` first; "Remove" → DELETE `/api/v1/tenants/{id}` with `window.confirm` first
- Empty state: "No tenants provisioned yet"

Use `useAras()` for `api` and `notify`. Check `user.is_admin` — redirect to `/` if not admin. Register route and lazy import in `ui/src/App.tsx` (add `<Route path="admin/tenants" element={<TenantAdmin />} />`).

### F2: POS receipt panel after charge
UPDATE `ui/src/views/PosView.tsx` — after a successful `quick_invoice` response, set receipt state instead of calling `clearCart()` immediately.

Add state:
```tsx
const [receipt, setReceipt] = useState<(QuickInvoiceResult & { items: CartLine[] }) | null>(null)
```

On successful charge: `setReceipt({ ...result, items: [...cart] })` — do NOT call `clearCart()` yet.

Show receipt panel (replaces the charge section in the right column when `receipt != null`):
- Invoice number (large, bold)
- Item rows: `item.name | qty × formatCurrency(price) | line total`
- Divider, Subtotal row
- If not credit mode: "Paid" + "Change" rows
- If credit mode: badge "Credit — AR/AP created"
- Print button → `window.print()` (add `print:block` on receipt, `print:hidden` on item grid)
- "New Transaction" button → `setReceipt(null); clearCart()`

## Claude Review
APPROVED

---

## Agent Reports

### Backend (Gemini)
- files_written: api/apps/erp/pot/services/pot.py, api/apps/erp/pot/models.py
- features_added: PotSession.orders relationship restored with back_populates on both sides
- fixes_applied: Removed stale PosSession import block; replaced db.query().get() with db.get(); get_shift_report and close_session use explicit PotOrder queries
- framework_changes: none
- issues: none

### Frontend (Gemini)
- files_written: ui/src/views/TenantAdmin.tsx, ui/src/views/PosView.tsx, ui/src/App.tsx
- features_added: TenantAdmin page at /admin/tenants (list/provision/seed/deprovision); POS receipt panel; /admin/tenants route + lazy import
- fixes_applied: none
- framework_changes: none
- issues: PosView.tsx had structural corruption — receipt state undeclared, orphaned JSX block outside component close, dangling )} in JSX

## Claude Review
- verdict: NEEDS-FIX (fixed inline)
- reviewed_by: Claude Sonnet 4.6
- date: 2026-05-19

## Revision Tasks (completed inline)
- [x] PosView.tsx: added `receipt` useState declaration (type: QuickInvoiceResult & items/paid/change/isCredit/mode)
- [x] PosView.tsx: replaced dangling `)}` before `</aside>` with full receipt panel JSX (invoice number, item rows, totals, credit badge, Print + New Transaction buttons)
- [x] PosView.tsx: removed orphaned JSX block (lines 437–505) that appeared after component closing brace

---

## Next Task: Remove dead PotOrder models

> Written by: Claude Code (claude-sonnet-4-6)
> Date: 2026-05-19
> Feature: PotOrder cleanup

## Context

POS flow creates invoices directly (`quick_invoice` → InflowInvoice/OutflowInvoice with `pos_session_id`). PotSession computed fields (`total_sales`, `total_purchase`, `invoice_count`, `payment_summary`) already aggregate from invoices. PotOrder/PotOrderLine/PotPaymentLine serve no purpose in the current architecture and should be removed.

## Backend Tasks

### B1: Delete dead models + service methods
DELETE `PotOrder`, `PotOrderLine`, `PotPaymentLine` from `api/apps/erp/pot/models.py`.
Remove their imports and the `PotSession.orders` relationship (there are no orders anymore).
Remove `PotPaymentLine` import from the top of the file.

UPDATE `api/apps/erp/pot/services/pot.py` — remove `process_order`, `open_session`, `close_session`, `get_shift_report`, and `get_pot_products` methods entirely. Remove `PotOrder, PotOrderLine, PotPaymentLine, PotTerminal` from imports (keep only `PotSession`). Remove `ModeOfPayment` import. The class can be empty or deleted if no methods remain.

UPDATE `api/apps/erp/pot/views.py` — remove `PotOrderView` and `PotOrderLineView` classes and their imports.

`shift_report` model action on `PotSession` calls `PotService.get_shift_report`. Rewrite it to use the computed fields that already exist on the session:
```python
@Aras.model_action(name="shift_report", permission="read", label="Shift Report")
def shift_report(self, db):
    from sqlalchemy.orm import object_session
    s = object_session(self)
    return ok({
        "session_id": self.id,
        "session_number": self.number,
        "status": self.status,
        "total_sales": self.total_sales,
        "total_purchase": self.total_purchase,
        "invoice_count": self.invoice_count,
        "payment_summary": self.payment_summary,
        "opening_balance": float(self.opening_balance or 0),
        "closing_balance": float(self.closing_balance or 0),
    }, message="Shift Report")
```

After changes run `cd api && python manage.py sync` — auto_migrate will NOT drop the old tables (drop is manual), but the models will be unregistered from the UI.

---

## Agent Reports

### Backend (Gemini)
- files_written: api/apps/erp/pot/models.py, api/apps/erp/pot/services/pot.py, api/apps/erp/pot/views.py, api/apps/erp/pot/app.py
- features_added: none
- fixes_applied: Removed dead PotOrder, PotOrderLine, and PotPaymentLine models, views, and service methods. Rewrote shift_report model action on PotSession to use computed fields. Removed removed models from pot/app.py and re-synced metadata.
- framework_changes: none
- issues: none

## Gemini Review
- verdict: APPROVED
- reviewed_by: Gemini
- date: 2026-05-19


## Claude Review
- verdict: APPROVED
- reviewed_by: Claude Sonnet 4.6
- date: 2026-05-19
- notes: PotOrder/PotOrderLine/PotPaymentLine removed. PotService is empty stub (pass). shift_report uses computed fields. PotOrderView/PotOrderLineView gone. Files verified.
