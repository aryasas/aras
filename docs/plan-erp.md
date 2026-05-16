# Framework Refinements + ERP App Skeleton Plan

## Context

The old `aras-old/app/erp/` (~9.3k LOC, 7 sub-apps, ~50 models, ~15 service files) is on the legacy Flask/`ArasGen` stack and cannot be copy-ported. Domain logic (accounting posting, stock WAC, multi-company, doc numbering, fiscal periods) is sound and must be **re-implemented** under the new FastAPI/`Aras` framework — not copy-edited.

Before porting, the framework needs six small primitives that every ERP module will rely on. These are foundational and generic enough that **any future app** (HR, project, ticketing) will reuse them — they are not ERP-specific. After framework work, this plan creates the empty 6-app skeleton (`erp_config`, `erp_stock`, `erp_accounting`, `erp_crm`, `erp_supplier`, `erp_pos`) ready for incremental porting in a follow-up plan.

**Intended outcome:**
1. Framework gains `__unique_together__`, `info={"choices":[...]}`, generic `__scoped_by__` feature, opt-in `is_active` (`activatable`) + form-hide rules, **enforced three-layer class inheritance with abstract ERP base mixins** (`DocumentBase`, `LineItemBase`, `MasterDataBase`, `ConfigBase`), and `on_transition` workflow callbacks.
2. Six empty ERP apps registered, dependency order documented, `python manage.py sync` clean.
3. Old `aras-old/app/erp/` remains untouched as the porting reference.

---

## Part A — Framework Refinements

### A1. `__unique_together__` composite unique constraints

**File:** `api/core/base/model.py`

In `Model.__init_subclass__`, after the existing registry logic, read `__unique_together__: list[tuple[str, ...]]` and append `UniqueConstraint(*cols, name=f"uq_{tablename}_{'_'.join(cols)}")` to `cls.__table_args__`. Merge with any existing tuple/dict form of `__table_args__`.

**Usage:**
```python
class StockProduct(Aras.Model):
    __tablename__ = "erp_stock_products"
    __unique_together__ = [("company_id", "code")]
```

**Why framework:** Pure schema concern, lives in `__init_subclass__`, zero business logic.

---

### A2. `choices` metadata for dropdown rendering

**Files:**
- `api/core/logic/ui_generator.py` — when serializing a column to field metadata, if `column.info.get("choices")` exists, emit `{ "type": "select", "options": [...] }` in the field descriptor.
- `api/core/logic/router_factory.py` — in the Pydantic schema generator (~line 66), if `info["choices"]` exists, narrow the type to `Literal[*choices]` so validation rejects bad values.

**Usage:**
```python
valuation_method: Mapped[str] = mapped_column(
    String(20),
    info={"choices": ["standard", "average", "fifo"], "default_label": "Average"},
)
```

**Why framework:** UI rendering + validation are both framework concerns. No app duplication.

---

### A3. Generic `__scoped_by__` scoping feature

This replaces the ERP-only "multi-company" idea with a generic tenant/company/workspace primitive.

**Declaration (on model):**
```python
class StockProduct(Aras.Model):
    __tablename__ = "erp_stock_products"
    __scoped_by__ = [("company_id", "erp_config_companies")]
    __features__ = ["audit", "scoped"]
```

**Files to create / modify:**

1. **`api/core/logic/scope.py` (NEW)** — `ScopeContext` request-scoped object holding current scope values (dict like `{"company_id": 3}`). Resolves from JWT claims via `get_current_scope(user)` helper.

2. **`api/core/logic/trait_injector.py`** — add `_inject_scoped(target_cls)` branch. For each `(col, fk_table)` in `__scoped_by__`, mapped_column an `Integer ForeignKey(f"{fk_table}.id"), nullable=False, index=True` if not already declared on the class. Append to `__unique_together__` auto-derivation candidates.

3. **`api/core/auth/service.py`** — extend JWT `create_access_token` payload with `scope: {"company_id": user.current_company_id, ...}`. Read into `request.state.scope` in `get_current_user`.

4. **`api/core/auth/router.py`** — add `POST /api/auth/switch-scope` endpoint: validates user has access to the requested scope value, re-issues JWT with updated `scope` claim.

5. **`api/core/logic/router_factory.py`**:
   - In list/get queries, if `model_class.__scoped_by__` set, append `WHERE col = current_scope[col]` filters from `request.state.scope`.
   - In create/update, auto-inject scope values onto the payload before persist (overriding any client-supplied value).
   - In `/metadata`, expose scope columns as `readonly: true` so forms hide them.

6. **`api/core/manager/sync_manager.py`** — sync writes `scoped_by` array into the `ResourceModel` registry row for frontend.

**Frontend (deferred to porting phase):** `ScopeContext` provider in `ui/src/aras-core/`, a scope switcher widget in topbar reading from `useAras()`.

**Why framework:** Identical pattern for every future multi-tenant feature. Generalizing now avoids ERP-shaped coupling.

---

### A4. Optional `is_active` + form-clean defaults

**Problem:** `api/core/base/model.py:72` hard-codes `is_active` on **every** model. For line-item / immutable / pivot tables (invoice lines, journal lines, payment allocations, M2M bridges, stock movement lines) this is nonsense — there is no semantic "disable" for a posted journal line. It also pollutes auto-generated forms with a useless checkbox and the default list query (`_q`, line 105) silently excludes "inactive" rows of tables that should never have that concept.

**Solution:** Make `is_active` an opt-in feature, not a baseline column.

**Files:**

1. **`api/core/base/model.py`**:
   - Remove `is_active` from the base `Model` (delete line 72).
   - Move it into `TraitInjector._inject_activatable` (new), triggered by `__features__ = ["activatable"]`.
   - Remove `is_active` from `_SYSTEM` set (line 96) — it's no longer guaranteed.
   - In `_q` (line 99-106), only apply the `is_active` filter if the column actually exists on the class: `if active_only and hasattr(cls, "is_active"): stmt = stmt.where(cls.is_active == True)`.

2. **`api/core/logic/trait_injector.py`** — add `_inject_activatable(target_cls)` that mapped_columns `is_active: Mapped[bool] = mapped_column(default=True, server_default="1")`.

3. **`api/core/logic/router_factory.py:62`** — remove the special-case `column.name == 'is_active'`; it's no longer always present.

4. **`api/core/logic/ui_generator.py:89`** — remove the `column.name != 'is_active'` carve-out for the same reason.

**Hide-by-default rule for forms:**

Add `info={"form_hidden": True}` support in `ui_generator.py`. The auto-form generator excludes these from the rendered form (still visible in detail view / API). Use it for:
- system columns: `created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at` (already excluded from create/update; also hide from edit form display).
- scope columns from `__scoped_by__` — auto-marked `form_hidden=True` since they come from request scope.
- `id` — primary key, never editable.

**Form simplification rules (codified in `docs/aras.md`):**

| Table type | Use `activatable`? | Notes |
|---|---|---|
| Master data (Product, Customer, Supplier, Account) | ✅ Yes | Disable instead of delete to preserve FK references. |
| Configuration (Currency, Charge, Uom, ProductCategory) | ✅ Yes | Same reason. |
| Documents (Invoice, Order, Payment, Movement) | ❌ No | Use `workflow` status (Draft/Posted/Cancelled). |
| Line items / details (InvoiceLine, JournalLine, OrderLine, MovementLine) | ❌ No | Cascade with parent; no independent state. |
| Pivot / M2M bridge (ProductCategory link, RolePermission) | ❌ No | Existence = membership. |
| Logs / immutable history (ActivityLog, JournalEntry once posted) | ❌ No | Immutable by design. |

**Why framework:** `is_active` is a framework primitive, but making it universal was wrong. Making it opt-in eliminates form clutter across ~40% of ERP tables.

---

### A5. Class inheritance rules (abstract mixins + layered hierarchy)

**Problem:** The framework supports `__abstract__ = True` on `Model` itself (line 27) but the inheritance contract is undocumented and **not used**. Without rules, the ERP port will repeat fields across dozens of models — e.g. every Document needs `number`, `date`, `company_id`, `status`, `currency_id`; every Line needs `parent_id`, `sequence`, `product_id`, `qty`, `uom_id`, `amount`. Without abstract bases this is ~600 lines of copy-paste across 6 ERP apps.

**Solution:** Codify a strict, three-layer inheritance rule that mirrors `docs/aras.md` section 2 ("Inheritance Hierarchy"), and provide app-level abstract bases ERP modules build on.

**Three-layer rule (enforced by lint + `__init_subclass__` validation):**

```
Level 1  Aras                  (root — decorators, registry hooks)
Level 2  Aras.Model            (CRUD, metadata, traits)  — __abstract__ = True
Level 3a App abstract mixins   (DocumentBase, LineItemBase, MasterDataBase, ConfigBase)  — __abstract__ = True, no __tablename__
Level 3b Concrete model        (SalesInvoice, StockProduct, ...) — exactly one __tablename__
```

**Rules:**
1. **A concrete model inherits from exactly ONE Level-3a abstract base + `Aras.Model`** (via the base). It MUST declare `__tablename__`. It MUST NOT redeclare columns the base already provides.
2. **A Level-3a abstract base sets `__abstract__ = True`, has no `__tablename__`, and defines columns/features common to its class.** It MUST NOT be registered (the existing `__init_subclass__` already skips `__abstract__` classes — verified).
3. **No diamond inheritance.** A concrete model picks one abstract base — `DocumentBase` OR `LineItemBase`, never both. Validate in `__init_subclass__`: count Level-3a ancestors; raise if > 1.
4. **No skipping levels.** A concrete model inheriting `Aras.Model` directly is allowed only for trivial models (config singletons). For ERP, lint warns.
5. **Features are additive, not overriding.** `__features__` on the concrete class is **appended** to (not replaces) the base's features. New behavior in `Model.__init_subclass__`: `cls.__features__ = list(dict.fromkeys(sum([getattr(b, "__features__", []) for b in cls.__mro__], [])))`.
6. **`__scoped_by__`, `__unique_together__`, `__layout__` are merged from MRO** the same way (deduped, child wins on conflict).

**File:** `api/core/base/model.py`
- In `__init_subclass__` (line 33), after step 1, add:
  - Inheritance validation: count Level-3a abstract ancestors; raise `TypeError` if > 1.
  - Merge `__features__`, `__scoped_by__`, `__unique_together__`, `__layout__` from MRO before TraitInjector runs.
- Add module docstring documenting the three-layer rule.

**App-level abstract bases (NEW files, not part of framework — live under shared ERP lib):**

```
api/apps/_erp_base/                  # NEW shared package (underscore prefix = not an app)
├── __init__.py
├── document.py                      # class DocumentBase(Aras.Model): __abstract__ = True
├── line_item.py                     # class LineItemBase(Aras.Model): __abstract__ = True
├── master_data.py                   # class MasterDataBase(Aras.Model): __abstract__ = True
└── config.py                        # class ConfigBase(Aras.Model): __abstract__ = True
```

Sketch:
```python
# api/apps/_erp_base/document.py
class DocumentBase(Aras.Model):
    __abstract__ = True
    __features__ = ["audit", "workflow", "scoped"]
    __scoped_by__ = [("company_id", "erp_config_companies")]

    number: Mapped[str] = mapped_column(String(32), info={"form_hidden": True})  # auto-naming
    doc_date: Mapped[date] = mapped_column(Date, default=date.today)
    status: Mapped[str] = mapped_column(String(20), default="Draft",
                                        info={"choices": ["Draft","Confirmed","Posted","Cancelled"]})
    currency_id: Mapped[int] = mapped_column(ForeignKey("erp_config_currencies.id"))
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
```

```python
# api/apps/_erp_base/line_item.py
class LineItemBase(Aras.Model):
    __abstract__ = True
    __features__ = ["audit"]   # NO activatable, NO workflow, NO scoped (inherits from parent doc)

    sequence: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    qty: Mapped[float] = mapped_column(Float, default=0)
    amount: Mapped[float] = mapped_column(Float, default=0)
    # Concrete subclass defines parent_id (FK to its specific doc) + __parent__ tablename
```

```python
# api/apps/_erp_base/master_data.py
class MasterDataBase(Aras.Model):
    __abstract__ = True
    __features__ = ["audit", "activatable", "scoped"]
    __scoped_by__ = [("company_id", "erp_config_companies")]

    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(200))
    # subclass adds __unique_together__ = [("company_id", "code")]
```

```python
# api/apps/_erp_base/config.py
class ConfigBase(Aras.Model):
    __abstract__ = True
    __features__ = ["audit", "activatable"]   # global config — NOT scoped by company

    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(200))
```

**Why this belongs alongside framework refinements:** the merge-from-MRO behavior (rule 5, 6) and the abstract-ancestor validation (rule 3) are **framework** changes to `Model.__init_subclass__`. The four mixin files under `api/apps/_erp_base/` are **shared app code** but must exist before any ERP module is ported, so they ship with this plan.

**Documentation:** `docs/aras.md` gets a new section "Class Inheritance Contract" with the rules above and a one-page diagram of which ERP model uses which base.

---

### A6. `on_transition` workflow callback hook

**File:** `api/core/manager/workflow_manager.py`

After step 2 (`item.status = transition["to"]`) and before return, fire callbacks:

```python
callbacks = TransitionRegistry.get(item.__class__, transition["from"], transition["to"])
for cb in callbacks:
    cb(db=db, item=item, user=user, transition=transition)
```

**New:** `api/core/logic/transition_registry.py` — `TransitionRegistry` class with `@Aras.on_transition(from_="Draft", to="Posted")` decorator that registers a callable per (model, from, to) triple. Decorator surfaced on `Aras` root in `api/core/base/aras.py`.

**Usage (app code):**
```python
@Aras.on_transition(model=SalesInvoice, from_="Draft", to="Posted")
def post_invoice_to_gl(db, item, user, transition):
    from .services.posting import post_sales_invoice
    post_sales_invoice(db, item.id)
```

**Why framework:** Workflow already lives in framework; without this hook every app re-implements the trigger via `model_action`. Tiny addition, huge leverage for accounting/stock posting.

---

## Part B — ERP App Skeleton

### Folder layout (under `api/apps/`)

```
api/apps/erp
├── config/         (was erp_config — kept)
├── stock/          (was erp_stock — kept)
├── accounting/     (was erp_acc — RENAMED)
├── crm/            (was erp_crm — kept)
├── supplier/       (was erp_sup — RENAMED)
└── pos/            (was erp_pos — kept)
```

The legacy `erp_main` is dissolved — its contents redistributed:
- `DocSeries`, `FiscalYear`, `FiscalPeriod`, `ModeOfPayment` → **`erp_config`**
- `ErpRole`, `ErpPermission` → drop; use framework's existing RBAC (`api/core/logic/permissions.py`)

The existing flat `api/apps/erp/` (Product/Customer/Order toy) is **deleted** — those are replaced by proper modules.

### Table naming convention (strict)

`erp_<module>_<table>` — e.g. `erp_stock_products`, `erp_accounting_sales_invoices`, `erp_config_companies`, `erp_supplier_purchase_orders`, `erp_pos_terminals`, `erp_crm_customers`.

### Per-app skeleton files

Each app gets only:
```
api/apps/erp/<module>/
├── __init__.py
├── app.py              # Aras.App subclass, models = []
└── models.py           # empty pass; ready for porting
```

`services/`, `views.py`, `schemas.py` added during porting, not skeleton.

### Dependency order (for the porting follow-up plan)

```
1. config       (Company, Currency, FxRate, Charge, DocSeries, FiscalYear, ModeOfPayment, Attachment)
2. stock        (Uom, ProductCategory, Product, Location, Movement, PriceList)
3. accounting   (Account, JournalEntry, SalesOrder, SalesInvoice, PurchaseInvoice, Payment)
4. crm          (CustomerGroup, Customer, Contact, Lead, Pipeline, Activity)
5. supplier     (SupplierGroup, Supplier, PurchaseOrder)
6. pos          (Terminal, Session, ShiftEntry)
```

---

## Critical files (modify)

| File | Change |
|---|---|
| `api/core/base/model.py` | Read `__unique_together__` in `__init_subclass__`, append to `__table_args__`. Validate single Level-3a abstract ancestor; merge `__features__`/`__scoped_by__`/`__unique_together__`/`__layout__` from MRO. |
| `api/core/logic/trait_injector.py` | Add `_inject_scoped` branch reading `__scoped_by__`. |
| `api/core/logic/ui_generator.py` | Emit `choices` in column metadata; emit `scoped_by` at model level. |
| `api/core/logic/router_factory.py` | Apply scope filter to queries; inject scope on writes; `Literal[*choices]` in schema. |
| `api/core/manager/workflow_manager.py` | Fire `TransitionRegistry` callbacks after status update. |
| `api/core/base/model.py` (again) | Remove baseline `is_active` column; drop from `_SYSTEM`; gate `_q` filter on existence. |
| `api/core/logic/router_factory.py` (again) | Drop `is_active` special-case (line 62). |
| `api/core/logic/ui_generator.py` (again) | Drop `is_active` carve-out (line 89); honor `info={"form_hidden": True}`. |
| `api/core/manager/sync_manager.py` | Persist `scoped_by` to ResourceModel registry. |
| `api/core/auth/service.py` | Include `scope` claim in JWT; resolve `request.state.scope`. |
| `api/core/auth/router.py` | Add `/switch-scope` endpoint. |
| `api/core/base/aras.py` | Expose `Aras.on_transition` decorator. |

## Critical files (create)

| File | Purpose |
|---|---|
| `api/core/logic/scope.py` | `ScopeContext`, resolver. |
| `api/core/logic/transition_registry.py` | `TransitionRegistry` + decorator. |
| `api/apps/erp/base/{__init__.py,document.py,line_item.py,master_data.py,config.py}` | Shared abstract mixins for ERP modules. |
| `api/apps/erp/config/{__init__.py,app.py,models.py}` | Skeleton. |
| `api/apps/erp/stock/{__init__.py,app.py,models.py}` | Skeleton. |
| `api/apps/erp/accounting/{__init__.py,app.py,models.py}` | Skeleton. |
| `api/apps/erp/crm/{__init__.py,app.py,models.py}` | Skeleton. |
| `api/apps/erp/supplier/{__init__.py,app.py,models.py}` | Skeleton. |
| `api/apps/erp/pos/{__init__.py,app.py,models.py}` | Skeleton. |

## Critical files (delete)

| File | Why |
|---|---|
| `api/apps/erp/` (entire folder) | Replaced by 6 properly-scoped apps. |

---

## Existing utilities to reuse (do NOT reinvent)

- `api/core/base/model.py:33-62` — `__init_subclass__` registry hook (extend, don't replace).
- `api/core/logic/trait_injector.py:16-29` — feature dispatcher (add new branch).
- `api/core/manager/workflow_manager.py:46-78` — `trigger_action` (extend, don't rewrite).
- `api/core/logic/router_factory.py:32-86` — Pydantic schema generator (add `Literal` branch).
- `api/core/logic/permissions.py` — RBAC; do NOT create `ErpRole`/`ErpPermission` from old code.
- `api/core/manager/audit_manager.py` — reference pattern for `__features__`-driven framework hooks.

---

## Verification

### Framework refinements
1. `cd api && python manage.py sync` — clean exit, no Alembic errors. Verify `is_active` column dropped from line-item / pivot tables that don't opt in.
2. `cd api && pytest tests/ -k "scope or transition or unique_together or choices or activatable or inheritance" -v` — new tests for each primitive (create alongside implementation).
3. Manual: define a throwaway test model with `__scoped_by__ = [("company_id", "erp_config_companies")]`, log in as a user with `current_company_id=1`, hit `GET /api/<table>` — verify only company-1 rows return. Switch via `POST /api/auth/switch-scope {"company_id": 2}`, repeat — verify only company-2 rows.
4. Workflow: define a test model with a Draft→Posted transition, register `@Aras.on_transition`, trigger via `POST /api/<table>/{id}/action/post` — verify callback fires and side-effect lands.

### ERP skeleton
1. `python manage.py sync` after creating each app — verify each app registers in `app_metadata` table.
2. Hit `GET /api/apps/erp` — verify all 6 ERP apps appear with correct labels/icons.
3. UI sidebar shows 6 ERP apps; clicking each shows empty model list (expected — no models yet).
4. `tests/test_auth_security.py` still passes (no regression in auth).

### Done when
- All 6 framework primitives (A1–A6) green in tests.
- All 6 ERP apps register cleanly with no models.
- Old `api/apps/erp/` removed.
- **`docs/aras.md`** updated with the six new primitives (`__unique_together__`, `choices`, `__scoped_by__`, `activatable`/`form_hidden`, inheritance contract + `_erp_base` mixins, `@Aras.on_transition`) and the `services/` convention noted as the documented app pattern. **MANDATORY per CLAUDE.md change-logging rule — any framework change requires aras.md update.**
- **`docs/feature.md`** entry under `## Framework Refinements (2026-05-15)` listing each primitive + the 6 ERP skeleton apps. **MANDATORY per CLAUDE.md change-logging rule — any feature added requires feature.md update.**

---

## Execution strategy (post-`/clear`)

This plan is meant to be executed in a fresh session. Suggested approach to save tokens:

1. **Read only this plan** (`docs/plan-erp.md`) and the **CLAUDE.md** + **docs/aras.md** quickly. Skip `aras-old/` entirely (reference only when porting, which is out of scope here).
2. **Order of work** — finish each primitive before starting the next; commit/sync after each so failures are isolated:
   1. A1 `__unique_together__` (smallest, validates the `__init_subclass__` extension pattern)
   2. A4 opt-in `is_active` (touches `model.py` + `trait_injector.py` — pairs naturally with A1)
   3. A5 inheritance rules + `_erp_base` mixins (depends on A4 because mixins declare `__features__ = ["activatable"]`)
   4. A2 `choices` (small, isolated, ui_generator + router_factory)
   5. A3 `__scoped_by__` (largest — JWT/auth changes; do after the others are stable)
   6. A6 `on_transition` (smallest hook, last)
3. **Part B ERP skeleton** — only after all 6 primitives pass tests. Delete `api/apps/erp/` last (after the 6 new apps register cleanly).
4. **After each primitive**: append to `docs/feature.md` and `docs/aras.md` immediately (don't batch — CLAUDE.md rule is mandatory).
5. **Token discipline**: never re-read `aras-old/` files; never re-read `api/core/base/aras.py` (use `docs/framework_ref.md`). Use `grep` for symbols, `Read` with offset/limit for files >300 lines.
6. **If approaching token limit**: stop, write `docs/progress.md` with which primitives are done + which test file proves it, then `/clear`.

---

## Out of scope (follow-up plan)

- Porting model fields from `aras-old/` into the 6 apps.
- Service files (`posting.py`, `stock_compute.py`, `coa_resolver.py`, `price.py`, `doc_series.py`).
- Frontend `ScopeContext` provider + topbar scope switcher.
- Print templates, fiscal-period auto-reversal, POS hardware drivers.
