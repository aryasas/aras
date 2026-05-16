# Claude Plan — ERP Core Completion

Branch: `feature/erp-core-completion`
Last commit: `6a5f1c0`

---

## Selesai ✅

### Commit 6a5f1c0 — Payment, Order, Delivery, CRM

- **AccPayment + AccPaymentAllocation** — menggantikan `AccInvoicePayment`; 1 payment bisa dialokasikan ke N invoice
- **SalesOrder** (`acc_sales_order`) + lines + charges + service (`confirm_order`, `create_invoice_from_order`)
- **PurchaseOrder** (`sup_purchase_order`) + lines + charges + service
- **DeliveryTrip + DeliveryOrder** (`stk_delivery_*`) + service (`create_from_invoice/order`, `assign_to_trip`, `mark_delivered`)
- **CRM lead conversion** — `convert_to_customer` di `lead_service.py`
- **Hapus** `vendor_name`, `vendor_ref` dari `AccPurchaseInvoice`
- **Tambah** `origin_order_id` FK di Sales/Purchase Invoice
- **Manifest** — semua ResourceDef, handler, dan custom route baru terdaftar
- **Migration 026** — semua tabel baru + migrasi data `acc_invoice_payment` → drop

---

## Antrian 📋

### 1. ActionDef — Automasi CustomRoute (PRIORITAS)

Saat ini setiap action di `manifest.py` butuh:
- Handler function `_handle_*` (boilerplate: parse JSON, try/except, jsonify)
- Entry manual `CustomRoute(path, handler, methods)`

**Tujuan:** ganti dengan `ActionDef` di dalam `ResourceDef`:

```python
ResourceDef("acc/sales-order", SalesOrder,
    actions=[
        ActionDef("confirm",        sales_order_service.confirm_order,        "POST"),
        ActionDef("create-invoice", sales_order_service.create_invoice_from_order, "POST"),
    ]
)
```

Framework auto-mount ke `/api/erp/acc/sales-order/confirm/` + wrap try/except + jsonify.

**Files yang perlu diubah:**
- `arasCore/lib/services/app_helper.py` — tambah class `ActionDef`; update `ResourceDef` + `AppHelper`
- `arasCore/lib/services/blueprints.py` — baca `res.actions`, mount otomatis
- `aras/erp/manifest.py` — refactor semua `_handle_*` + `CustomRoute` → `ActionDef`

**Backward compatible:** `custom_routes` tetap ada untuk edge case (URL args `<int:id>`, dll).

---

### 2. Rename Plan — docs/rename-plan.md (TERAKHIR, saat siap production)

Catat rename map lengkap tabel + class. Tidak ada kode yang disentuh sekarang.

Prefix final yang disepakati: `erp_<modul>_<nama>` untuk tabel ERP,
framework tetap `aras_*`, `adm_*`, `mgr_*`, `auth_*`, `gen_*`.

Contoh:
| Sekarang | Nanti |
|----------|-------|
| `company` | `erp_main_company` |
| `currency` | `erp_main_currency` |
| `stock_product` | `erp_stk_product` |
| `acc_sales_invoice` | `erp_acc_sales_invoice` |
| `pos_order` | `erp_pos_order` |

---

### 3. Generic Deletion Dialog + Backup/Restore (NEXT)

**Tujuan:** Saat delete dokumen yang punya linked docs (misal PurchaseOrder → Invoice → JournalEntry), sistem:
1. Auto-detect linked docs dan tampilkan dialog (hanya jika ada linked docs)
2. Backup semua ke `aras_deleted_doc` sebelum delete
3. Trash page untuk restore/permanent-delete

**Detection strategy:**
- Auto: SA relationships dengan `cascade='all, delete-orphan'` (ONETOMANY)
- Auto: `origin_model`/`origin_id` registry (model yang punya kolom `origin_model`)
- Manual opt-in: `__linked_docs__` class attribute untuk FK tanpa cascade

**Files baru (8):**
- `arasCore/lib/models/deletion_models.py` — `DeletedDoc` model + `_ORIGIN_MODEL_REGISTRY`
- `arasCore/lib/services/linked_doc_detector.py` — `detect_linked_docs(obj)` → `list[LinkedDocNode]`
- `arasCore/lib/services/deletion_service.py` — `inspect_deletion`, `execute_deletion`, `execute_restore`
- `arasCore/lib/migrations/m015_deleted_docs.py` — CREATE TABLE `aras_deleted_doc`
- `static/js/adm_delete.js` — modal JS (fetch linked-docs → show modal → confirm)
- `templates/admin/gen/modal_delete_confirm.html` — modal fragment
- `templates/admin/trash/trash_list.html` — Trash page
- `arasCore/admin/routes/trash.py` — `/admin/trash/`, `/trash/<id>/restore/`, `/trash/<id>/permanent-delete/`

**Files dimodifikasi (8):**
- `arasCore/lib/ui/admin_mount.py` — `make_delete()` + `make_bulk_delete()` → `execute_deletion`; `make_edit()` inject `linked_docs_url`
- `arasCore/admin/crud_factory.py` — action `"delete"` + `"bulk_delete"` → `execute_deletion`
- `arasCore/lib/services/api_handler.py` — DELETE handler → `execute_deletion`; tambah route `GET /<id>/linked-docs/`
- `arasCore/lib/blueprints.py` — auto-register `origin_model` models di `_register_helper()`
- `arasCore/__init__.py` — tambah `m015_deleted_docs.run(app)`
- `templates/admin/gen/gen_view_form.html` — tambah Delete button + include modal
- `templates/admin/base_index.html` — load `adm_delete.js`
- `arasCore/admin/routes/__init__.py` — import `trash` module

**State:** `[x] DONE`

---

### 4. Fitur yang Belum Ada (backlog)

- Report builder UI (engine sudah ada di `report_runner.py`)
- POS shift reconciliation → closing journal entry
- Lead → pipeline kanban view
- Purchase Order receive flow (partial receipt tracking via `qty_received`)
- Sales Order partial invoicing (tracking via `qty_invoiced` sudah ada di model)


Here is Claude's plan:                                                                                                                                                                         
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
Plan: Company is_default + BaseErpModel + FK Default Combobox Fix                                                                                                                              
                                                                                                                                                                                                 
Context                                                                                                                                                                                          
                                                                                                                                                                                                 
Three related features:                                                                                                                                                                          
1. Company.is_default — new field on Company. When set, new documents with a company_id field pre-fill with this company. Overridable per-user via ErpUserCompany.is_default (already exists).   
2. BaseErpModel — optional ERP base class developers can inherit to get company_id + common behavior without repeating boilerplate. Opt-in; existing models untouched.
3. FK default combobox fix — the admin column settings UI already has relation_filter and default_value fields, but the combobox to pick the FK default doesn't populate because JS doesn't pass
 relation_filter to the API, and the API doesn't apply it. Fix is completing the partial implementation.

---
Feature 1: Company.is_default

1.1 Model — aras/erp/erp_core/models/company.py

Add after is_group:
is_default = db.Column(db.Boolean, default=False, nullable=False)

Add before_save hook to enforce single default:
def before_save(self, is_new):
    if self.is_default:
        db.session.execute(
            db.text("UPDATE company SET is_default=0 WHERE id != :id"),
            {"id": self.id or 0}
        )

1.2 Migration — arasCore/lib/migrations/m017_relation_filter.py (already exists for relation_filter)

Create new: aras/erp/migrations/m_company_is_default.py
def run(flask_app):
    with flask_app.app_context():
        from arasCore.lib.core.extensions import db
        from sqlalchemy import text
        with db.engine.connect() as conn:
            exists = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='company' AND COLUMN_NAME='is_default'"
            )).scalar()
            if not exists:
                conn.execute(text("ALTER TABLE company ADD COLUMN is_default TINYINT(1) NOT NULL DEFAULT 0"))
                conn.commit()

1.3 Update _get_company_id() — aras/erp/views/core.py

Replace function body with priority chain:
1. ErpUserCompany.query.filter_by(user_id=current_user.id, is_default=True).first() → membership.company_id
2. Company.find(is_default=True, is_active=True) → company.id
3. Company.query.filter_by(is_active=True).order_by(Company.id).first() → fallback

---
Feature 2: BaseErpModel

New file: aras/erp/erp_core/models/base.py

from arasCore.lib.core.base_model import ArasModel, db

class BaseErpModel(ArasModel):
    __abstract__ = True
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)

    def get_company(self):
        from aras.erp.erp_core.models.company import Company
        return Company.get(self.company_id)

    def before_save(self, is_new):
        if is_new and not self.company_id:
            self.company_id = _resolve_default_company_id()


def _resolve_default_company_id():
    try:
        from flask_login import current_user
        from aras.erp.erp_core.models.acl import ErpUserCompany
        m = ErpUserCompany.query.filter_by(user_id=current_user.id, is_default=True).first()
        if m:
            return m.company_id
    except Exception:
        pass
    try:
        from aras.erp.erp_core.models.company import Company
        c = Company.find(is_default=True, is_active=True)
        if c:
            return c.id
        c = Company.query.filter_by(is_active=True).order_by(Company.id).first()
        return c.id if c else None
    except Exception:
        return None

Note: No company relationship on abstract base (causes SQLAlchemy mapper conflicts). Each concrete model keeps its own relationship.

Update _get_company_id() in aras/erp/views/core.py to reuse _resolve_default_company_id:

def _get_company_id():
    from aras.erp.erp_core.models.base import _resolve_default_company_id
    return _resolve_default_company_id()

Export — aras/erp/erp_core/models/__init__.py

Add: from .base import BaseErpModel

---
Feature 3: Fix FK Default Combobox

Problem

The admin column settings panel has relation_filter (SQL WHERE snippet) and default_value fields. When the user sets a relation column, a combobox should appear to pick the default FK value.
It doesn't work because:
- JS _loadFkChoices() does not pass relation_filter to the API
- API endpoint api_fk_choices() does not accept or apply relation_filter

3.1 JS fix — static/js/adm_columns.js

In _loadFkChoices(currentDefault), after building the base URL, add:
var relFilter = (form.elements['relation_filter'] && form.elements['relation_filter'].value) || '';
if (relFilter) url += '&relation_filter=' + encodeURIComponent(relFilter);

3.2 API fix — arasCore/admin/routes/apps.py in api_fk_choices()

Add param reading:
relation_filter = request.args.get("relation_filter", "").strip()

Apply to query before fetching rows — use text() WHERE clause if relation_filter is provided:
if relation_filter:
    # relation_filter is a trusted admin-only SQL snippet (e.g. "is_group = 0")
    rows = rows.filter(db.text(relation_filter))

Note: relation_filter is set only by admins in column settings — not user input. Still sanitize by rejecting values containing ;, --, DROP, INSERT, UPDATE, DELETE (basic guard).

3.3 Run migration m017_relation_filter.py

This migration adds relation_filter to mgr_column — it's already written, just needs to be run.

---
Files Changed

┌─────────────────────────────────────────────┬────────────────────────────────────────────────────┐
│                    File                     │                       Change                       │
├─────────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ aras/erp/erp_core/models/company.py         │ Add is_default column + before_save hook           │
├─────────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ aras/erp/erp_core/models/base.py            │ New — BaseErpModel + _resolve_default_company_id() │
├─────────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ aras/erp/erp_core/models/__init__.py        │ Export BaseErpModel                                │
├─────────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ aras/erp/views/core.py                      │ Update _get_company_id()                           │
├─────────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ aras/erp/migrations/m_company_is_default.py │ New — migration for company.is_default             │
├─────────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ static/js/adm_columns.js                    │ Pass relation_filter to FK choices API             │
├─────────────────────────────────────────────┼────────────────────────────────────────────────────┤
│ arasCore/admin/routes/apps.py               │ Accept + apply relation_filter in api_fk_choices() │
└─────────────────────────────────────────────┴────────────────────────────────────────────────────┘

---
Verification

1. Set a company is_default=True in Company form → confirm DB has only one row with is_default=1
2. Create a new document (e.g. Customer) → company_id pre-fills with the default company
3. Log in as a user with ErpUserCompany.is_default set → their company takes priority over Company.is_default
4. In admin column settings, set a relation column with relation_filter = "is_group = 0" → the default value combobox shows only non-group companies
