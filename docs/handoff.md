# Handoff Spec — Customize Add Field · Rename doc_series · Delete+Nav in Form · Stock Ledger in Item
> run_id: 13

> run_id: 14
> Written by: Claude Code (claude-sonnet-4-6)
> Date: 2026-05-19

---

## Context

Four independent tasks. Can be implemented in parallel.

---

## Task 1 — Fix "Add Field" button in Customize panel

**Problem:** `ListView` inside `handleCustomize` (DynamicForm.tsx) has no `onAdd` — clicking Add does nothing.

UPDATE `ui/src/aras-core/components/DynamicForm.tsx`

In `handleCustomize`, add `onAdd` to the existing `<ListView key={resourceRecord.id} ...>`:

```tsx
onAdd={() => {
  showPanel(
    `New Field — ${vocabulary.get(metadata.title)}`,
    <DynamicForm
      resource="aras_fields"
      id="new"
      initialData={{ resource_id: resourceRecord.id }}
      onSave={() => {
        notify("Field added. Refresh to see changes.", "success");
        setRefreshTrigger(prev => prev + 1);
        closePanel();
      }}
      onCancel={closePanel}
    />,
    'max-w-4xl'
  );
}}
```

Also add `initialData?: Record<string, any>` to `DynamicFormProps`. When `id === 'new'`, merge `initialData` into `formData` on mount (inside the `fetchData` useEffect, after the empty-form branch).

---

## Task 2 — Rename aras_naming_series to doc_series

**2a. UPDATE `api/core/registry/series.py`**
Change: `__tablename__ = "aras_naming_series"` to `__tablename__ = "doc_series"`

**2b. UPDATE `api/core/manager/health_manager.py`**
Change the string `"aras_naming_series"` to `"doc_series"`

**2c. NEW FILE `api/core/migrations/rename_naming_series.py`**

```python
"""Rename aras_naming_series to doc_series. Run BEFORE manage.py sync."""
import sys
sys.path.insert(0, ".")
from core.lib.database import SessionLocal

SQL = """
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'aras_naming_series')
  AND NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'doc_series')
  THEN
    ALTER TABLE aras_naming_series RENAME TO doc_series;
    RAISE NOTICE 'Renamed aras_naming_series to doc_series';
  ELSE
    RAISE NOTICE 'No rename needed';
  END IF;
END $$;
"""

def run():
    db = SessionLocal()
    try:
        db.execute(SQL)
        db.commit()
        print("Done.")
    finally:
        db.close()

if __name__ == "__main__":
    run()
```

---

## Task 3 — Delete button + Back/Next navigation in DynamicForm

UPDATE `ui/src/aras-core/components/DynamicForm.tsx`

### 3a — Add props and delete handler

Add to DynamicFormProps:
```ts
onDelete?: () => void;
onNavigate?: (id: number) => void;
```

Add delete handler:
```ts
const handleDelete = async () => {
  if (\!currentId) return;
  const confirmed = await confirm('Delete this record? This cannot be undone.');
  if (\!confirmed) return;
  try {
    const cleanResource = metadata?.api_path || cleanResourcePath(resource);
    await api.delete(`/${cleanResource}/${currentId}`);
    notify('Record deleted.', 'success');
    if (onDelete) onDelete();
    else if (onCancel) onCancel();
  } catch (err: any) {
    notify(err.response?.data?.detail || 'Delete failed', 'error');
  }
};
```

### 3b — Back/Next state and effect

Add state:
```ts
const [prevId, setPrevId] = useState<number | null>(null);
const [nextId, setNextId] = useState<number | null>(null);
```

Add effect (depends on currentId + metadata):
```ts
useEffect(() => {
  if (\!currentId || \!metadata) { setPrevId(null); setNextId(null); return; }
  const base = metadata.api_path || cleanResourcePath(resource);
  const id = Number(currentId);
  api.get(`/${base}`, { params: { per_page: 1, order_by: 'id', desc: true,
    filters: JSON.stringify([{ field: 'id', op: '<', value: id }]) }})
    .then(r => setPrevId(r.data?.data?.items?.[0]?.id ?? null)).catch(() => setPrevId(null));
  api.get(`/${base}`, { params: { per_page: 1, order_by: 'id', desc: false,
    filters: JSON.stringify([{ field: 'id', op: '>', value: id }]) }})
    .then(r => setNextId(r.data?.data?.items?.[0]?.id ?? null)).catch(() => setNextId(null));
}, [currentId, metadata]);
```

### 3c — Render toolbar buttons

Import ChevronLeft, ChevronRight, Trash2 from lucide-react. Add to toolbar (alongside Settings button):

```tsx
{currentId \!= null && (
  <button onClick={handleDelete} title="Delete record"
    className="p-2 hover:bg-rose-50 rounded-xl text-rose-400 hover:text-rose-600 transition-colors">
    <Trash2 size={20} />
  </button>
)}
{currentId \!= null && (
  <>
    <button onClick={() => prevId && onNavigate?.(prevId)} disabled={\!prevId}
      title="Previous record"
      className="p-2 hover:bg-slate-50 rounded-xl text-slate-400 disabled:opacity-30 transition-colors">
      <ChevronLeft size={20} />
    </button>
    <button onClick={() => nextId && onNavigate?.(nextId)} disabled={\!nextId}
      title="Next record"
      className="p-2 hover:bg-slate-50 rounded-xl text-slate-400 disabled:opacity-30 transition-colors">
      <ChevronRight size={20} />
    </button>
  </>
)}
```

### 3d — Wire in DynamicView

UPDATE `ui/src/views/DynamicView.tsx`:
```tsx
<DynamicForm
  resource={resource}
  id={id}
  onSave={() => navigate(basePath)}
  onCancel={() => navigate(basePath)}
  onDelete={() => navigate(basePath)}
  onNavigate={(newId) => navigate(`${basePath}/${newId}`)}
/>
```

---

## Task 4 — Stock on-hand in Items form with per-location breakdown

### 4a — Fix stock calculation

UPDATE `api/apps/erp/stock/services/stock.py`

Current compute_qty only counts inflows (to_location_id). Rewrite to subtract outflows (from_location_id):

```python
@staticmethod
def compute_qty(db: Session, item_id: int, location_id: int = None) -> float:
    from sqlalchemy import case as sa_case
    base = db.query(StockMovementLine).join(StockMovement).filter(
        StockMovementLine.item_id == item_id,
        StockMovement.status == "Posted",
    )
    if location_id:
        base = base.filter(
            (StockMovementLine.to_location_id == location_id) |
            (StockMovementLine.from_location_id == location_id)
        )
        signed = func.sum(sa_case(
            (StockMovementLine.to_location_id == location_id, StockMovementLine.qty),
            (StockMovementLine.from_location_id == location_id, -StockMovementLine.qty),
            else_=0.0
        ))
    else:
        # total: inflows minus outflows; internal transfers cancel automatically
        signed = func.sum(
            sa_case((StockMovementLine.to_location_id.isnot(None), StockMovementLine.qty), else_=0.0)
            - sa_case((StockMovementLine.from_location_id.isnot(None), StockMovementLine.qty), else_=0.0)
        )
    return float(base.with_entities(signed).scalar() or 0)

@staticmethod
def compute_qty_by_location(db: Session, item_id: int) -> list:
    from ..models import Location
    from sqlalchemy import union_all, select
    in_q = select(
        StockMovementLine.to_location_id.label("loc_id"),
        StockMovementLine.qty.label("qty")
    ).join(StockMovement).where(
        StockMovementLine.item_id == item_id,
        StockMovement.status == "Posted",
        StockMovementLine.to_location_id.isnot(None)
    )
    out_q = select(
        StockMovementLine.from_location_id.label("loc_id"),
        (-StockMovementLine.qty).label("qty")
    ).join(StockMovement).where(
        StockMovementLine.item_id == item_id,
        StockMovement.status == "Posted",
        StockMovementLine.from_location_id.isnot(None)
    )
    combined = union_all(in_q, out_q).subquery()
    rows = db.query(
        combined.c.loc_id,
        Location.name,
        func.sum(combined.c.qty).label("net_qty")
    ).join(Location, Location.id == combined.c.loc_id) \
     .group_by(combined.c.loc_id, Location.name) \
     .having(func.sum(combined.c.qty) \!= 0).all()
    return [{"location_id": r.loc_id, "location_name": r.name, "qty": float(r.net_qty)} for r in rows]
```

### 4b — Add stock endpoint

UPDATE `api/apps/erp/stock/app.py` — add router and register in Stock.routers:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.lib.database import get_db
from core.response import ok

stock_extra_router = APIRouter()

@stock_extra_router.get("/items/{item_id}/stock")
def get_item_stock(item_id: int, db: Session = Depends(get_db)):
    from .services.stock import StockComputeService
    return ok({
        "total": StockComputeService.compute_qty(db, item_id),
        "by_location": StockComputeService.compute_qty_by_location(db, item_id),
    })
```

Add stock_extra_router to Stock.routers list.

### 4c — Add stock_by_location computed field to Item

UPDATE `api/apps/erp/stock/models.py` — add after qty_on_hand in Item class:

```python
@Aras.computed_field
def stock_by_location(self) -> list:
    from .services.stock import StockComputeService
    from sqlalchemy.orm import object_session
    db = object_session(self)
    if not db: return []
    return StockComputeService.compute_qty_by_location(db, self.id)
```

### 4d — Show in Item view layout

UPDATE `api/apps/erp/stock/views.py` — insert after the "general" section in ItemView.layout:

```python
{"key": "stock", "title": "Stock", "fields": ["qty_on_hand", "stock_by_location"]},
```

### 4e — Render stock_by_location in DynamicForm

UPDATE `ui/src/aras-core/components/DynamicForm.tsx` — in renderField, add before the generic Component fallback:

```tsx
if (field.name === 'stock_by_location') {
  const rows: { location_name: string; qty: number }[] =
    Array.isArray(formData[field.name]) ? formData[field.name] : [];
  return (
    <div key={field.name} className="flex flex-col gap-1.5 md:col-span-2">
      <label className="text-sm font-bold text-slate-700">Stock by Location</label>
      {rows.length === 0
        ? <p className="text-sm text-slate-400 italic">No stock recorded</p>
        : (
          <table className="w-full text-sm border border-slate-200 rounded-xl overflow-hidden">
            <thead className="bg-slate-50 text-slate-600 text-xs uppercase">
              <tr>
                <th className="px-3 py-2 text-left font-semibold">Location</th>
                <th className="px-3 py-2 text-right font-semibold">Qty on Hand</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-3 py-2">{r.location_name}</td>
                  <td className="px-3 py-2 text-right font-mono text-slate-800">{r.qty}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )
      }
    </div>
  );
}
```

---

## Agent Reports

## Gemini (Gemini 2.5 Flash)
- Backend implementation of Task 2 and Task 4 complete.
- Renamed `aras_naming_series` to `doc_series` in `series.py` and `health_manager.py`.
- Created and ran `api/core/migrations/rename_naming_series.py`.
- Rewrote `StockComputeService.compute_qty` to correctly handle inflows/outflows and internal transfers.
- Added `StockComputeService.compute_qty_by_location`.
- Added `stock_extra_router` with `/items/{item_id}/stock` endpoint.
- Added `stock_by_location` computed field to `Item` model.
- Updated `ItemView` layout to include the `stock` section.
- Ran `manage.py sync` to update the registry.


---
## Agent Reports (2026-05-19)

### Backend (Gemini 2.5 Flash)
- files_written: none
- features_added: none
- fixes_applied: none
- framework_changes: none
- issues: none

### Frontend (Codex GPT-5.5)
- files_written: ui/src/aras-core/components/DynamicForm.tsx, ui/src/views/DynamicView.tsx
- features_added: Add Field panel creation, form delete action, previous/next record navigation, stock by location rendering
- fixes_applied: DynamicView now handles delete and record navigation callbacks
- framework_changes: none
- issues: none

## Claude Review
- verdict: APPROVED
- reviewed_by: Claude Code
- date: 2026-05-19
- notes: <!-- none or describe -->

