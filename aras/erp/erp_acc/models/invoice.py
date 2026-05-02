from arasCore.lib.core.base_model import ArasModel, db


class AccSalesInvoice(ArasModel):
    __tablename__ = "acc_sales_invoice"
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
    company_id       = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    name             = db.Column(db.String(50), nullable=False)
    customer_id      = db.Column(db.Integer, db.ForeignKey("crm_customer.id"), nullable=True)
    location_id      = db.Column(db.Integer, db.ForeignKey("stock_location.id"), nullable=True)
    origin_order_id  = db.Column(db.BigInteger, db.ForeignKey("acc_sales_order.id"), nullable=True)
    pos_session_id   = db.Column(db.Integer, db.ForeignKey("pos_session.id"), nullable=True)
    invoice_date     = db.Column(db.Date, nullable=False)
    due_date         = db.Column(db.Date, nullable=True)
    currency_id      = db.Column(db.Integer, db.ForeignKey("currency.id"), nullable=False)
    fiscal_period_id = db.Column(db.Integer, db.ForeignKey("fiscal_period.id"), nullable=True)
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
    charges       = db.relationship("AccSalesInvoiceCharge", backref="invoice",
                                    cascade="all, delete-orphan")
    allocations   = db.relationship("AccPaymentAllocation",
                                    primaryjoin="AccPaymentAllocation.sales_invoice_id==AccSalesInvoice.id",
                                    cascade="all, delete-orphan")

    @property
    def amount_paid(self):
        return sum(float(a.amount) for a in self.allocations)

    @property
    def amount_due(self):
        return max(0, float(self.total) - self.amount_paid)

    def __repr__(self):
        return f"<SalesInvoice {self.name} [{self.state}]>"


class AccSalesInvoiceLine(ArasModel):
    __tablename__ = "acc_sales_invoice_line"
    __footer_totals__ = ["subtotal"]
    __display_fields__ = ("description",)
    __price_type__    = "sales"
    __price_api_path__ = "/api/erp/invoice/product-price"
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


class AccSalesInvoiceCharge(ArasModel):
    __tablename__ = "acc_sales_invoice_charge"

    id         = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    invoice_id = db.Column(db.BigInteger, db.ForeignKey("acc_sales_invoice.id"), nullable=False)
    charge_id  = db.Column(db.Integer, db.ForeignKey("charge.id"), nullable=False)
    sequence   = db.Column(db.Integer, default=10)
    base_amt   = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    amount     = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    account_id = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)

    charge  = db.relationship("Charge")
    account = db.relationship("AccAccount")


class AccPurchaseInvoice(ArasModel):
    __tablename__ = "acc_purchase_invoice"
    __readonly_fields__ = {"subtotal", "discount_amt", "charge_amt", "total", "journal_entry_id", "pos_session_id"}
    __linked_docs__ = [
        {"model_name": "AccJournalEntry", "fk_field": "journal_entry_id", "fk_on_self": True},
    ]
    __table_args__ = (
        db.Index("ix_pur_inv_company_date", "company_id", "invoice_date"),
        db.Index("ix_pur_inv_state", "state"),
    )

    id               = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    company_id       = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    supplier_id      = db.Column(db.Integer, db.ForeignKey("sup_supplier.id"), nullable=True)
    location_id      = db.Column(db.Integer, db.ForeignKey("stock_location.id"), nullable=True)
    origin_order_id  = db.Column(db.BigInteger, db.ForeignKey("sup_purchase_order.id"), nullable=True)
    pos_session_id   = db.Column(db.Integer, db.ForeignKey("pos_session.id"), nullable=True)
    name             = db.Column(db.String(50), nullable=False)
    invoice_date     = db.Column(db.Date, nullable=False)
    due_date         = db.Column(db.Date, nullable=True)
    currency_id      = db.Column(db.Integer, db.ForeignKey("currency.id"), nullable=False)
    fiscal_period_id = db.Column(db.Integer, db.ForeignKey("fiscal_period.id"), nullable=True)
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
    charges       = db.relationship("AccPurchaseInvoiceCharge", backref="invoice",
                                    cascade="all, delete-orphan")
    allocations   = db.relationship("AccPaymentAllocation",
                                    primaryjoin="AccPaymentAllocation.purchase_invoice_id==AccPurchaseInvoice.id",
                                    cascade="all, delete-orphan")

    @property
    def amount_paid(self):
        return sum(float(a.amount) for a in self.allocations)

    @property
    def amount_due(self):
        return max(0, float(self.total) - self.amount_paid)

    def __repr__(self):
        return f"<PurchaseInvoice {self.name} [{self.state}]>"


class AccPurchaseInvoiceLine(ArasModel):
    __tablename__ = "acc_purchase_invoice_line"
    __footer_totals__ = ["subtotal"]
    __display_fields__ = ("description",)
    __price_type__    = "purchase"
    __price_api_path__ = "/api/erp/invoice/product-price"
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


class AccPurchaseInvoiceCharge(ArasModel):
    __tablename__ = "acc_purchase_invoice_charge"

    id         = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    invoice_id = db.Column(db.BigInteger, db.ForeignKey("acc_purchase_invoice.id"), nullable=False)
    charge_id  = db.Column(db.Integer, db.ForeignKey("charge.id"), nullable=False)
    sequence   = db.Column(db.Integer, default=10)
    base_amt   = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    amount     = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    account_id = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)

    charge  = db.relationship("Charge")
    account = db.relationship("AccAccount")
