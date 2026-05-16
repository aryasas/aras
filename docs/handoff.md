# Handoff Spec

> Written by: Claude Code (claude-sonnet-4-6)
> Date: 2026-05-16
> Feature: Go 1+2 — Auto-discovery, Saved Filters, Inventory Valuation, GL Reconciliation, Toast Queue, Dark Mode Charts, Service Return Type Consistency

---

## Context
Six improvements across backend and frontend: auto-discover ERP app models, saved filter persistence, FIFO inventory valuation service, GL reconciliation action, persistent toast notification queue, dark mode chart support, and consistent service return types.

---

## Backend Tasks

### 1. Auto-discover models in app registrations

UPDATE `api/apps/erp/accounting/app.py` — replace the hand-written `models = [...]` list with auto-discovery:
```python
from core.logic.discovery import autodiscover_models
models = autodiscover_models(__name__, [
    "models", "models_grn"
])
```
Do the same for any other ERP sub-app that has a manual `models = [...]` list longer than 5 entries (check `stock/app.py`, `config/app.py`, `party/app.py`, `hr/app.py`, `asset/app.py`).

NEW FUNCTION in `api/core/logic/discovery.py` — add `autodiscover_models(package_name: str, module_names: list[str]) -> list`:
- Import each module in `module_names` relative to `package_name`
- Collect all subclasses of `Aras.Model` defined in those modules (filter out imported ones via `__module__`)
- Return the list

### 2. Saved Filters

NEW FILE `api/apps/erp/base/saved_filter.py` — `SavedFilter` model:
```python
class SavedFilter(MasterDataBase):
    __tablename__ = "erp_base_saved_filters"
    resource: Mapped[str] = mapped_column(String(100))   # e.g. "erp_accounting_accounts"
    name: Mapped[str] = mapped_column(String(100))
    filters_json: Mapped[str] = mapped_column(Text)       # JSON blob of filter state
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
```
Register in the ERP base app (`api/apps/erp/app.py` — add `SavedFilter` to models).

NEW FILE `api/apps/erp/base/saved_filter_router.py` — custom router:
- `GET /erp/saved-filters?resource=<tablename>` → list filters for resource + org
- `POST /erp/saved-filters` → create `{resource, name, filters_json, is_default}`
- `DELETE /erp/saved-filters/{id}` → delete

Register router in `api/apps/erp/app.py` under `routers = [...]`.

### 3. Inventory Valuation Service (FIFO)

NEW FILE `api/apps/erp/stock/services/valuation.py` — `InventoryValuationService`:
```python
class InventoryValuationService:
    @staticmethod
    def get_unit_cost(db: Session, product_id: int, org_id: int) -> float:
        """FIFO: return cost of oldest unconsumed stock layer."""
        ...

    @staticmethod
    def consume(db: Session, product_id: int, org_id: int, qty: float) -> float:
        """Consume qty units FIFO; return total cost consumed (for COGS)."""
        ...

    @staticmethod
    def receive(db: Session, product_id: int, org_id: int, qty: float, unit_cost: float):
        """Add a new stock layer on goods receipt."""
        ...
```

NEW FILE `api/apps/erp/stock/models_valuation.py` — `StockLayer` model:
```python
class StockLayer(DocumentBase):
    __tablename__ = "erp_stock_layers"
    product_id: FK → erp_stock_products.id
    qty_received: Mapped[float]
    qty_remaining: Mapped[float]
    unit_cost: Mapped[float]
    source_ref: Mapped[str] = mapped_column(String(50), nullable=True)  # e.g. "GRN-001"
```

UPDATE `api/apps/erp/accounting/services/posting.py`:
- Replace `unit_cost=inv_line.unit_price - inv_line.discount` (lines ~100, ~167) with `InventoryValuationService.consume(db, inv_line.product_id, org_id, inv_line.qty)` for COGS calculation
- Call `InventoryValuationService.receive(...)` when posting a GRN (GoodsReceiptNote lines)

Register `StockLayer` in `api/apps/erp/stock/app.py`.

### 4. GL Reconciliation Service

NEW FILE `api/apps/erp/accounting/services/reconciliation.py` — `ReconciliationService`:
```python
class ReconciliationService:
    @staticmethod
    def reconcile_account(db: Session, account_id: int, org_id: int) -> dict:
        """
        Match open invoice payments to GL entries for the given account.
        Returns: {matched: int, unmatched_gl: int, unmatched_payments: int}
        """
        ...

    @staticmethod
    def get_unreconciled(db: Session, account_id: int, org_id: int) -> list[dict]:
        """Return list of unreconciled GL entries for an account."""
        ...
```

UPDATE `api/apps/erp/accounting/models.py` — add `@Aras.action` on `Account`:
```python
@Aras.action(label="Reconcile", icon="GitMerge")
def reconcile(self, db):
    from .services.reconciliation import ReconciliationService
    result = ReconciliationService.reconcile_account(db, self.id, self.org_id)
    return {"message": f"Reconciled {result['matched']} entries. Unmatched GL: {result['unmatched_gl']}, Payments: {result['unmatched_payments']}"}
```

### 5. Service Return Type Consistency

UPDATE `api/apps/erp/accounting/services/posting.py` — all public methods must return `dict` with keys `{success: bool, message: str, journal_entry_id: int | None}`. Currently some return `None` or raw model.

UPDATE `api/apps/erp/stock/services/` — `StockComputeService` methods that return raw `float` should return `{"value": float, "unit": str}`.

---

## Frontend Tasks

### 1. Saved Filters UI

UPDATE `ui/src/aras-core/components/ListView.tsx`:
- Add "Save Filter" button in the filter toolbar (only visible when filters are active)
- On click: show inline input for filter name → `POST /api/v1/erp/saved-filters`
- Add "Saved Filters" dropdown in the toolbar: `GET /api/v1/erp/saved-filters?resource=<resource>` → list; clicking one applies it
- Add delete (×) on each saved filter entry

### 2. Toast Notification Queue with Persistence

UPDATE `ui/src/aras-core/contexts/NotificationContext.tsx`:
- Add `history: Notification[]` to context — notifications accumulate here (not removed on timeout)
- Persist `history` to `localStorage` key `aras.notifications` (last 50)
- Restore history on mount from localStorage
- Keep existing auto-dismiss behavior for the active toast stack

NEW FILE `ui/src/aras-core/components/NotificationHistory.tsx`:
- Bell icon button with unread badge count
- Dropdown panel listing persisted history (newest first)
- "Clear all" button

UPDATE `ui/src/layouts/` (wherever the topbar is rendered) — add `<NotificationHistory />` next to the existing notification stack.

### 3. Dark Mode Chart Support

UPDATE any file in `ui/src/views/` or `ui/src/aras-core/` that renders Recharts components (`BarChart`, `LineChart`, `PieChart`, `AreaChart`):
- Read `darkMode` from `useUIStore()`
- Pass theme-aware colors: stroke/fill use `darkMode ? '#94a3b8' : '#64748b'` for axes/labels, `darkMode ? '#1e293b' : '#ffffff'` for tooltip background
- Wrap `<ResponsiveContainer>` in a `div` with `className={darkMode ? 'dark' : ''}` if not already done

If no Recharts usage exists yet (confirmed by grep), add a note in the agent report and skip — do not invent chart usage.

---
<!-- ── Below this line is filled automatically by multi_agent.py + Claude ── -->

## Agent Reports (DATE)

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
- verdict: APPROVED
- reviewed_by: Claude Code (claude-sonnet-4-6)
- date: 2026-05-16
- notes: 3 post-agent fixes applied to ListView.tsx: literal newline in split('\n') string, wrong import path for Combobox (../../lib/Combobox → ./Combobox), wrong import for FormattingService (default → named export). Build passes clean (✓ 1854 modules). NotificationHistory.tsx, HeaderActions.tsx present. NotificationContext history+localStorage wired. No Recharts usage confirmed — dark mode chart task correctly skipped.


---
## Agent Reports (revision (2026-05-16))

### Backend (Gemini 2.5 Flash)
- files_written: api/apps/erp/base/saved_filter.py, api/apps/erp/base/saved_filter_router.py, api/apps/erp/stock/services/valuation.py, api/apps/erp/stock/models_valuation.py, api/apps/erp/accounting/services/reconciliation.py
- features_added: Auto-discovery for ERP app models; Saved Filters functionality (model, router, registration); FIFO Inventory Valuation Service; GL Reconciliation Service with model action; Consistent return types for posting and stock compute services.
- fixes_applied: none
- framework_changes: `autodiscover_models` function added to `api/core/logic/discovery.py`; updated `Aras.App` `models` loading logic for several ERP sub-apps.
- issues: none

### Frontend (Codex GPT-5.5)
- files_written: none
- features_added: none
- fixes_applied: none
- framework_changes: none
- issues: none

## Claude Review
- verdict: NEEDS-FIX
- reviewed_by: Claude Code (claude-sonnet-4-6)
- date: 2026-05-16
- notes: Backend files all present and wired. 3 bugs fixed post-agent: (1) `discovery.py` had top-level `from ..base.model import ArasModel` causing circular import — moved inside function + renamed to `Model`. (2) `autodiscover_models` received `__name__` = `apps.erp.accounting.app` (not a package) — fixed by stripping trailing `.app`. (3) `saved_filter_router.py` imported non-existent `ArasRouter` and `Aras.Auth` — fixed to use `APIRouter` + `get_current_user` from `core.auth.service`. `manage.py sync` now passes clean. Frontend tasks not yet done (Gemini only ran backend).

## Revision Tasks

### Frontend
UPDATE `ui/src/aras-core/components/ListView.tsx` — add Saved Filters UI (Save Filter button + dropdown to load/delete saved filters via `/api/v1/erp/saved-filters`)

UPDATE `ui/src/aras-core/contexts/NotificationContext.tsx` — add persistent `history` array, persist to `localStorage` key `aras.notifications` (last 50), restore on mount

NEW FILE `ui/src/aras-core/components/NotificationHistory.tsx` — bell icon button with unread badge, dropdown listing history newest-first, "Clear all" button

UPDATE topbar layout file — add `<NotificationHistory />` next to notification stack

UPDATE any Recharts-using file in `ui/src/views/` — pass dark-mode-aware colors from `useUIStore().darkMode`; if no Recharts usage found, note it and skip


---
## Agent Reports (revision (2026-05-16))

### Backend (Gemini 2.5 Flash)
- files_written: none
- features_added: none
- fixes_applied: none
- framework_changes: none
- issues: none

### Frontend (Codex GPT-5.5)
- files_written: ui/src/aras-core/components/NotificationHistory.tsx, ui/src/layouts/components/HeaderActions.tsx
- features_added: Saved Filters UI, Persistent Toast Notification Queue.
- fixes_applied: none
- framework_changes: none
- issues: No Recharts components were found in the codebase, so the "Dark Mode Chart Support" task was skipped as per instructions.

## Claude Review
- verdict: <!-- APPROVED / NEEDS-FIX -->
- reviewed_by: Claude Code
- date: <!-- fill -->
- notes: <!-- none or describe -->

## Revision Tasks
<!-- If verdict is NEEDS-FIX, list tasks here then re-run multi_agent.py -->
<!-- Delete this section if APPROVED -->
