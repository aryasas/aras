# Handoff — Aras Framework Refactoring (Phase 1–3)

## Context
Consolidate repeated patterns across backend and frontend into a shared utility bank: `db_session` property on Model, `math_utils` for ERP line calculations, `TradeDocumentBase` consolidating InflowInvoice/OutflowInvoice (~90% shared code), strategy-pattern handlers, and frontend hooks (`useModel`, `useListView`, `useFormState`).

---

## Backend Tasks

### Phase 1 — Core Utilities

- UPDATE `api/core/base/model/__init__.py` — add `db_session` property:
  ```python
  @property
  def db_session(self):
      from sqlalchemy.orm import object_session
      return object_session(self)
  ```
  Then grep all `db = object_session(self)` usages in `api/apps/` and replace with `db = self.db_session`.

- NEW FILE `api/core/lib/math_utils.py` — ERP calculation helpers:
  - `line_amount(qty, unit_price, discount) -> float` — `qty * (unit_price - discount)`
  - `line_total(qty, unit_price, discount) -> float` — same, cast to float
  - `apply_percent_charge(subtotal, rate) -> float` — `subtotal * (rate / 100.0)`
  - `invoice_total(subtotal, total_tax, total_charge) -> float`

  Then update all call sites:
  - `api/apps/accounting/services/recalc_mixin.py` lines 21, 33, 49
  - `api/apps/accounting/handlers.py` lines 81, 130, 194, 225
  - `api/apps/pot/models.py` lines 38, 52 (raw SQL — leave as-is, note in docstring)

### Phase 2 — TradeDocument Base Class (High Risk)

- NEW FILE `api/apps/base/trade_document.py` — `TradeDocumentBase(DocumentBase)` with `__abstract__ = True`:
  - Shared columns from both `InflowInvoice` and `OutflowInvoice`: `party_id`, `currency`, `subtotal`, `total_tax`, `total_charge`, `total_amount`, `status`, `due_date`, `notes`, `series_id`, `grn_id` (if applicable)
  - Shared computed fields: `amount_paid`, `amount_due`
  - Shared actions: `create_invoice` (abstract or shared logic), `post` (delegated to subclass via abstract method)
  - Abstract methods that subclasses MUST implement: `get_gl_side()` → `"debit"/"credit"`, `get_payment_type()` → `"receivable"/"payable"`, `get_stock_movement_type()` → string
  - `DocumentRecalcMixin` stays as-is (already extracted in `services/recalc_mixin.py`)

- UPDATE `api/apps/accounting/models.py`:
  - `InflowInvoice` inherits `TradeDocumentBase, DocumentRecalcMixin` — remove all fields/methods now in base, implement abstract methods: `get_gl_side() → "credit"`, `get_payment_type() → "receivable"`, `get_stock_movement_type() → "outgoing"`
  - `OutflowInvoice` inherits `TradeDocumentBase, DocumentRecalcMixin` — same cleanup, implement: `get_gl_side() → "debit"`, `get_payment_type() → "payable"`, `get_stock_movement_type() → "incoming"`
  - Keep `__tablename__` unchanged on both concrete classes
  - Keep `InflowInvoiceLine`, `OutflowInvoiceLine`, `InflowInvoiceCharge`, `OutflowInvoiceCharge` as-is (separate refactor)

### Phase 3 — Handler Strategy Pattern

- UPDATE `api/apps/accounting/handlers.py`:
  - Remove all `isinstance(item, InflowInvoice)` / `isinstance(item, OutflowInvoice)` branches
  - Replace with calls to `item.get_gl_side()`, `item.get_payment_type()`, `item.get_stock_movement_type()` — these are now provided by `TradeDocumentBase` implementations
  - `source_type` string: use `item.__class__.__name__` instead of hardcoded `"InflowInvoice"` / `"OutflowInvoice"`
  - Result: one generic `post_invoice_gl(item, db, params)` function, no branching on type

---

## Frontend Tasks

- NEW FILE `ui/src/hooks/useModel.ts` — typed API fetch hook (implement first, others depend on it):
  ```ts
  useModel<T>(resource: string, id?: string | number) -> {
    data: T | null,
    list: T[],
    loading: boolean,
    error: string | null,
    fetch: () => void,
    fetchList: (params?: Record<string, unknown>) => void,
    save: (payload: Partial<T>) => Promise<T>,
    remove: (id: string | number) => Promise<void>,
  }
  ```
  Uses `useAras().api` internally. Base URL: `/api/v1/${resource}`.

- NEW FILE `ui/src/hooks/useListView.ts` — depends on `useModel`:
  ```ts
  useListView<T>(resource: string) -> {
    rows: T[],
    loading: boolean,
    page: number,
    pageSize: number,
    total: number,
    sortField: string | null,
    sortOrder: "asc" | "desc",
    filters: Record<string, unknown>,
    setPage, setPageSize, setSort, setFilters,
    refresh: () => void,
  }
  ```

- NEW FILE `ui/src/hooks/useFormState.ts` — depends on `useModel`:
  ```ts
  useFormState<T>(resource: string, id?: string | number) -> {
    values: Partial<T>,
    dirty: boolean,
    saving: boolean,
    error: string | null,
    setValue: (field: keyof T, value: unknown) => void,
    reset: () => void,
    submit: () => Promise<T>,
  }
  ```

---

## Verification

- Run `pytest api/tests/` after Phase 2 — must pass before starting Phase 3
- Smoke test exists at `api/apps/accounting/tests/` — ensure inflow + outflow invoice post end-to-end
- After Phase 3, re-run full suite
- No DB migrations needed — `TradeDocumentBase` uses `__abstract__ = True`, columns stay on child tables
- If `__abstract__` is ever removed or changed to joined-table inheritance in future: a data migration will be required — document this in the class docstring

---

## Out of Scope

- Auth/permission layer
- Multi-tenant schema logic
- Print and report routers
- Any module outside `api/apps/accounting/` for Phase 2
- `InflowInvoiceLine` / `OutflowInvoiceLine` consolidation (separate plan)

---

## Agent Reports
