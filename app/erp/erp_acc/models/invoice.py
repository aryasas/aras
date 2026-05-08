from arasCore.arasgen import ArasGen
from app.erp.erp_acc.manifest import Acc
from arasCore.lib.core.base_model import ArasModel, db


def _recalc_invoice_totals(inv):
    """Compute subtotal/charge_amt/total from child lines.
    discount_amt is user-entered on the header. Charges sum from inv.charges.
    """
    sub = 0.0
    for ln in (inv.lines or []):
        q = float(ln.qty or 0)
        p = float(ln.unit_price or 0)
        d = float(ln.discount_pct or 0)
        ln.subtotal = round(q * p * (1 - d / 100.0), 4)
        sub += float(ln.subtotal or 0)
    ch = sum(float(c.amount or 0) for c in (inv.charges or []))
    inv.subtotal    = round(sub, 4)
    inv.charge_amt  = round(ch, 4)
    inv.total       = round(sub + ch - float(inv.discount_amt or 0), 4)


def _postable_invoice_context(obj, post_url, res_key):
    """Shared logic for sales/purchase invoice form sidebar."""
    state = getattr(obj, "state", None)
    try:
        from arasCore.lib.services.workflow import get_workflow, get_available_actions
        from flask_login import current_user
        wf = get_workflow(res_key)
        if wf:
            actions = get_available_actions(current_user, obj, wf)
            return {
                "obj_state": state,
                "workflow_actions": actions,
                "workflow_resource_key": res_key,
                "obj_id": obj.id,
            }
    except Exception:
        pass
    if state == "draft":
        return {"post_url": post_url, "obj_id": obj.id}
    return {"obj_state": state}


class AccSalesInvoice(ArasGen.Model, module=Acc):
    __title__     = "Sales Invoices"
    __icon__      = "fa-file-text-o"
    __menu_order__= 1
    __tablename__ = "acc_sales_invoice"
    __naming_series__ = "SINV-{YYYY}-{####}"
    __readonly_fields__ = {"subtotal", "discount_amt", "charge_amt", "total", "journal_entry_id", "pos_session_id"}
    __linked_docs__ = [
        {"model_name": "AccJournalEntry", "fk_field": "journal_entry_id", "fk_on_self": True},
    ]
    __table_args__ = (
        db.Index("ix_sal_inv_company_date", "company_id", "invoice_date"),
        db.Index("ix_sal_inv_customer", "customer_id"),
        db.Index("ix_sal_inv_state", "state"),
    )

    id               = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    company_id       = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=False)
    name             = db.Column(db.String(50), nullable=False)
    customer_id      = db.Column(db.Integer, db.ForeignKey("crm_customer.id"), nullable=True)
    location_id      = db.Column(db.Integer, db.ForeignKey("stock_location.id"), nullable=True)
    origin_order_id  = db.Column(db.BigInteger, db.ForeignKey("acc_sales_order.id"), nullable=True)
    pos_session_id   = db.Column(db.Integer, db.ForeignKey("pos_session.id"), nullable=True)
    invoice_date     = db.Column(db.Date, nullable=False)
    due_date         = db.Column(db.Date, nullable=True)
    currency_id      = db.Column(db.Integer, db.ForeignKey("cfg_currency.id"), nullable=False)
    fiscal_period_id = db.Column(db.Integer, db.ForeignKey("main_fiscal_period.id"), nullable=True)
    subtotal         = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    discount_amt     = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    charge_amt       = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    total            = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    state            = db.Column(db.Enum("draft", "submitted", "posted", "partial", "paid", "cancelled"),
                                  default="draft", nullable=False)
    payment_term_days = db.Column(db.Integer, default=0)
    reference        = db.Column(db.String(100), nullable=True)
    notes            = db.Column(db.Text, nullable=True)
    price_type_id    = db.Column(db.Integer, db.ForeignKey("stock_price_type.id"), nullable=True)
    journal_entry_id = db.Column(db.BigInteger, db.ForeignKey("acc_journal_entry.id"), nullable=True)

    company       = db.relationship("Company")
    customer      = db.relationship("CrmCustomer")
    currency      = db.relationship("Currency")
    location      = db.relationship("StockLocation", foreign_keys=[location_id])
    origin_order  = db.relationship("SalesOrder", foreign_keys=[origin_order_id])
    pos_session   = db.relationship("PosSession", foreign_keys=[pos_session_id])
    price_type    = db.relationship("StockPriceType", foreign_keys=[price_type_id])
    journal_entry = db.relationship("AccJournalEntry")
    lines         = db.relationship("AccSalesInvoiceLine", backref="invoice",
                                    cascade="all, delete-orphan")
    charges             = db.relationship("AccSalesInvoiceCharge", backref="invoice",
                                    cascade="all, delete-orphan")
    payment_allocations = db.relationship(
        "AccPaymentAllocation",
        primaryjoin="and_(AccPaymentAllocation.invoice_type=='sales', foreign(AccPaymentAllocation.invoice_id)==AccSalesInvoice.id)",
        lazy="dynamic",
        viewonly=True,
    )
    @property
    def allocations(self):
        return self.payment_allocations.all()

    @property
    def amount_paid(self):
        return sum(float(a.amount) for a in self.allocations)

    @property
    def amount_due(self):
        return max(0, float(self.total) - self.amount_paid)

    def __repr__(self):
        return f"<SalesInvoice {self.name} [{self.state}]>"

    def after_save(self, is_new=False):
        _recalc_invoice_totals(self)

    def detail_context(self, obj):
        if not obj:
            return {}
        return _postable_invoice_context(obj, "/api/erp/acc/posting/post_sales_invoice/", "erp/acc/sales-invoice")

class AccSalesInvoiceLine(ArasGen.Model, module=Acc):
    __is_child__  = True
    __tablename__ = "acc_sales_invoice_line"
    __footer_totals__ = ["subtotal"]
    __display_fields__ = ("description",)
    __price_type__    = "sales"
    __price_api_path__ = "/api/erp/acc/product_lookup/product_price"
    __vcols_exclude__  = {"sequence", "account_id", "is_active", "tax_id", "tax_amt"}

    id           = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    invoice_id   = db.Column(db.BigInteger, db.ForeignKey("acc_sales_invoice.id"), nullable=False)
    sequence     = db.Column(db.Integer, default=0)
    product_id   = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=True)
    description  = db.Column(db.String(255), nullable=False)
    qty          = db.Column(db.Numeric(12, 4), default=1, nullable=False)
    uom_id       = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=True)
    unit_price   = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    discount_pct = db.Column(db.Numeric(5, 2), default=0, nullable=False)
    subtotal     = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    account_id   = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)

    product = db.relationship("StockProduct")
    uom     = db.relationship("StockUom")
    account = db.relationship("AccAccount")


class AccSalesInvoiceCharge(ArasGen.Model, module=Acc):
    __is_child__  = True
    __tablename__ = "acc_sales_invoice_charge"

    id         = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    invoice_id = db.Column(db.BigInteger, db.ForeignKey("acc_sales_invoice.id"), nullable=False)
    charge_id  = db.Column(db.Integer, db.ForeignKey("cfg_charge.id"), nullable=False)
    sequence   = db.Column(db.Integer, default=10)
    base_amt   = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    amount     = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    account_id = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)

    charge  = db.relationship("Charge")
    account = db.relationship("AccAccount")


class AccPurchaseInvoice(ArasGen.Model, module=Acc):
    __title__     = "Purchase Invoices"
    __icon__      = "fa-file-o"
    __menu_order__= 1
    __tablename__ = "acc_purchase_invoice"
    __naming_series__ = "PINV-{YYYY}-{####}"
    __readonly_fields__ = {"subtotal", "discount_amt", "charge_amt", "total", "journal_entry_id", "pos_session_id"}
    __linked_docs__ = [
        {"model_name": "AccJournalEntry", "fk_field": "journal_entry_id", "fk_on_self": True},
    ]
    __table_args__ = (
        db.Index("ix_pur_inv_company_date", "company_id", "invoice_date"),
        db.Index("ix_pur_inv_state", "state"),
    )

    id               = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    company_id       = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=False)
    supplier_id      = db.Column(db.Integer, db.ForeignKey("sup_supplier.id"), nullable=True)
    location_id      = db.Column(db.Integer, db.ForeignKey("stock_location.id"), nullable=True)
    origin_order_id  = db.Column(db.BigInteger, db.ForeignKey("sup_purchase_order.id"), nullable=True)
    pos_session_id   = db.Column(db.Integer, db.ForeignKey("pos_session.id"), nullable=True)
    name             = db.Column(db.String(50), nullable=False)
    invoice_date     = db.Column(db.Date, nullable=False)
    due_date         = db.Column(db.Date, nullable=True)
    currency_id      = db.Column(db.Integer, db.ForeignKey("cfg_currency.id"), nullable=False)
    fiscal_period_id = db.Column(db.Integer, db.ForeignKey("main_fiscal_period.id"), nullable=True)
    subtotal         = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    discount_amt     = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    charge_amt       = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    total            = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    state            = db.Column(db.Enum("draft", "submitted", "posted", "partial", "paid", "cancelled"),
                                  default="draft", nullable=False)
    payment_term_days = db.Column(db.Integer, default=0)
    notes            = db.Column(db.Text, nullable=True)
    price_type_id    = db.Column(db.Integer, db.ForeignKey("stock_price_type.id"), nullable=True)
    journal_entry_id = db.Column(db.BigInteger, db.ForeignKey("acc_journal_entry.id"), nullable=True)

    company       = db.relationship("Company")
    supplier      = db.relationship("SupSupplier", foreign_keys=[supplier_id], lazy="select")
    location      = db.relationship("StockLocation", foreign_keys=[location_id])
    origin_order  = db.relationship("PurchaseOrder", foreign_keys=[origin_order_id])
    pos_session   = db.relationship("PosSession", foreign_keys=[pos_session_id])
    currency      = db.relationship("Currency")
    price_type    = db.relationship("StockPriceType", foreign_keys=[price_type_id])
    journal_entry = db.relationship("AccJournalEntry")
    lines         = db.relationship("AccPurchaseInvoiceLine", backref="invoice",
                                    cascade="all, delete-orphan")
    charges             = db.relationship("AccPurchaseInvoiceCharge", backref="invoice",
                                    cascade="all, delete-orphan")
    payment_allocations = db.relationship(
        "AccPaymentAllocation",
        primaryjoin="and_(AccPaymentAllocation.invoice_type=='purchase', foreign(AccPaymentAllocation.invoice_id)==AccPurchaseInvoice.id)",
        lazy="dynamic",
        viewonly=True,
    )
    @property
    def allocations(self):
        return self.payment_allocations.all()

    @property
    def amount_paid(self):
        return sum(float(a.amount) for a in self.allocations)

    @property
    def amount_due(self):
        return max(0, float(self.total) - self.amount_paid)

    def __repr__(self):
        return f"<PurchaseInvoice {self.name} [{self.state}]>"

    def after_save(self, is_new=False):
        _recalc_invoice_totals(self)

    def detail_context(self, obj):
        if not obj:
            return {}
        return _postable_invoice_context(obj, "/api/erp/acc/purchase_posting/post_purchase_invoice/", "erp/acc/purchase-invoice")

class AccPurchaseInvoiceLine(ArasGen.Model, module=Acc):
    __is_child__  = True
    __tablename__ = "acc_purchase_invoice_line"
    __footer_totals__ = ["subtotal"]
    __display_fields__ = ("description",)
    __price_type__    = "purchase"
    __price_api_path__ = "/api/erp/acc/product_lookup/product_price"
    __vcols_exclude__  = {"sequence", "account_id", "is_active", "tax_id", "tax_amt"}

    id           = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    invoice_id   = db.Column(db.BigInteger, db.ForeignKey("acc_purchase_invoice.id"), nullable=False)
    sequence     = db.Column(db.Integer, default=0)
    product_id   = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=True)
    description  = db.Column(db.String(255), nullable=False)
    qty          = db.Column(db.Numeric(12, 4), default=1, nullable=False)
    uom_id       = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=True)
    unit_price   = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    discount_pct = db.Column(db.Numeric(5, 2), default=0, nullable=False)
    subtotal     = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    account_id   = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)

    product = db.relationship("StockProduct")
    uom     = db.relationship("StockUom")
    account = db.relationship("AccAccount")


class AccPurchaseInvoiceCharge(ArasGen.Model, module=Acc):
    __is_child__  = True
    __tablename__ = "acc_purchase_invoice_charge"

    id         = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    invoice_id = db.Column(db.BigInteger, db.ForeignKey("acc_purchase_invoice.id"), nullable=False)
    charge_id  = db.Column(db.Integer, db.ForeignKey("cfg_charge.id"), nullable=False)
    sequence   = db.Column(db.Integer, default=10)
    base_amt   = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    amount     = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    account_id = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)

    charge  = db.relationship("Charge")
    account = db.relationship("AccAccount")


# Auto-fill `name` for sales/purchase invoices via SQLAlchemy before_insert
# (admin CRUD calls populate_obj after before_save; use insert event instead).
from sqlalchemy import event as _sa_event


def _autoname_invoice(prefix: str):
    def _handler(mapper, connection, target):
        if getattr(target, "name", None):
            return
        from datetime import date
        from sqlalchemy import text
        tbl = target.__class__.__tablename__
        try:
            year = date.today().year
            row = connection.execute(
                text("SELECT id, next_value, last_period, padding, format FROM main_doc_series "
                     "WHERE code=:c AND company_id IS NULL FOR UPDATE"),
                {"c": tbl},
            ).first()
            if row is None:
                connection.execute(
                    text("INSERT INTO main_doc_series (code, format, next_value, padding, "
                         "reset_period, last_period, is_active) VALUES "
                         "(:c, :f, 2, 4, 'yearly', :p, 1)"),
                    {"c": tbl, "f": prefix + "-{YYYY}-{####}", "p": str(year)},
                )
                num = 1
                pad = 4
            else:
                pad = row[3] or 4
                period = str(year)
                num = row[1] if row[2] == period else 1
                connection.execute(
                    text("UPDATE main_doc_series SET next_value=:nv, last_period=:p WHERE id=:id"),
                    {"nv": num + 1, "p": period, "id": row[0]},
                )
            target.name = f"{prefix}-{year:04d}-{num:0{pad}d}"
        except Exception:
            from datetime import datetime
            target.name = f"{prefix}-{datetime.utcnow():%Y%m%d%H%M%S}"
    return _handler


_sa_event.listen(AccSalesInvoice,    "before_insert", _autoname_invoice("SINV"))
_sa_event.listen(AccPurchaseInvoice, "before_insert", _autoname_invoice("PINV"))
