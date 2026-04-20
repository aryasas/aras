from arasCore.lib.base_model import ArasModel, db


class AccSalesInvoice(ArasModel):
    __tablename__ = "acc_sales_invoice"
    __table_args__ = (
        db.Index("ix_sal_inv_company_date", "company_id", "invoice_date"),
        db.Index("ix_sal_inv_customer", "customer_id"),
        db.Index("ix_sal_inv_state", "state"),
    )

    id               = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    company_id       = db.Column(db.Integer, db.ForeignKey("core_company.id"), nullable=False)
    name             = db.Column(db.String(50), nullable=False)               # INV/2024/00001
    customer_id      = db.Column(db.Integer, db.ForeignKey("crm_customer.id"), nullable=False)
    invoice_date     = db.Column(db.Date, nullable=False)
    due_date         = db.Column(db.Date, nullable=True)
    currency_id      = db.Column(db.Integer, db.ForeignKey("core_currency.id"), nullable=False)
    journal_id       = db.Column(db.Integer, db.ForeignKey("acc_journal.id"), nullable=True)
    fiscal_period_id = db.Column(db.Integer, db.ForeignKey("core_fiscal_period.id"), nullable=True)
    subtotal         = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    discount_amt     = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    tax_amt          = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    total            = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    amount_paid      = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    amount_due       = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    state            = db.Column(db.Enum("draft", "posted", "partial", "paid", "cancelled"),
                                 default="draft", nullable=False)
    payment_term_days = db.Column(db.Integer, default=0)
    reference        = db.Column(db.String(100), nullable=True)
    notes            = db.Column(db.Text, nullable=True)
    journal_entry_id = db.Column(db.BigInteger, db.ForeignKey("acc_journal_entry.id"), nullable=True)
    pos_order_id     = db.Column(db.BigInteger, db.ForeignKey("pos_order.id"), nullable=True)

    company       = db.relationship("CoreCompany")
    customer      = db.relationship("CrmCustomer")
    currency      = db.relationship("CoreCurrency")
    journal       = db.relationship("AccJournal")
    journal_entry = db.relationship("AccJournalEntry")
    lines         = db.relationship("AccSalesInvoiceLine", backref="invoice",
                                    cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SalesInvoice {self.name} [{self.state}]>"


class AccSalesInvoiceLine(ArasModel):
    __tablename__ = "acc_sales_invoice_line"

    id           = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    invoice_id   = db.Column(db.BigInteger, db.ForeignKey("acc_sales_invoice.id"), nullable=False)
    sequence     = db.Column(db.Integer, default=0)
    product_id   = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=True)
    description  = db.Column(db.String(255), nullable=False)
    qty          = db.Column(db.Numeric(12, 4), default=1, nullable=False)
    uom_id       = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=True)
    unit_price   = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    discount_pct = db.Column(db.Numeric(5, 2), default=0)
    tax_id       = db.Column(db.Integer, db.ForeignKey("core_tax.id"), nullable=True)
    tax_amt      = db.Column(db.Numeric(18, 4), default=0)
    subtotal     = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    account_id   = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)

    product = db.relationship("StockProduct")
    uom     = db.relationship("StockUom")
    tax     = db.relationship("CoreTax")
    account = db.relationship("AccAccount")


class AccPurchaseInvoice(ArasModel):
    __tablename__ = "acc_purchase_invoice"
    __table_args__ = (
        db.Index("ix_pur_inv_company_date", "company_id", "invoice_date"),
        db.Index("ix_pur_inv_state", "state"),
    )

    id               = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    company_id       = db.Column(db.Integer, db.ForeignKey("core_company.id"), nullable=False)
    name             = db.Column(db.String(50), nullable=False)               # BILL/2024/00001
    vendor_name      = db.Column(db.String(200), nullable=False)
    vendor_ref       = db.Column(db.String(100), nullable=True)
    invoice_date     = db.Column(db.Date, nullable=False)
    due_date         = db.Column(db.Date, nullable=True)
    currency_id      = db.Column(db.Integer, db.ForeignKey("core_currency.id"), nullable=False)
    journal_id       = db.Column(db.Integer, db.ForeignKey("acc_journal.id"), nullable=True)
    fiscal_period_id = db.Column(db.Integer, db.ForeignKey("core_fiscal_period.id"), nullable=True)
    subtotal         = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    discount_amt     = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    tax_amt          = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    total            = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    amount_paid      = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    amount_due       = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    state            = db.Column(db.Enum("draft", "posted", "partial", "paid", "cancelled"),
                                 default="draft", nullable=False)
    payment_term_days = db.Column(db.Integer, default=0)
    notes            = db.Column(db.Text, nullable=True)
    journal_entry_id = db.Column(db.BigInteger, db.ForeignKey("acc_journal_entry.id"), nullable=True)

    company       = db.relationship("CoreCompany")
    currency      = db.relationship("CoreCurrency")
    journal       = db.relationship("AccJournal")
    journal_entry = db.relationship("AccJournalEntry")
    lines         = db.relationship("AccPurchaseInvoiceLine", backref="invoice",
                                    cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PurchaseInvoice {self.name} [{self.state}]>"


class AccPurchaseInvoiceLine(ArasModel):
    __tablename__ = "acc_purchase_invoice_line"

    id           = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    invoice_id   = db.Column(db.BigInteger, db.ForeignKey("acc_purchase_invoice.id"), nullable=False)
    sequence     = db.Column(db.Integer, default=0)
    product_id   = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=True)
    description  = db.Column(db.String(255), nullable=False)
    qty          = db.Column(db.Numeric(12, 4), default=1, nullable=False)
    uom_id       = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=True)
    unit_price   = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    discount_pct = db.Column(db.Numeric(5, 2), default=0)
    tax_id       = db.Column(db.Integer, db.ForeignKey("core_tax.id"), nullable=True)
    tax_amt      = db.Column(db.Numeric(18, 4), default=0)
    subtotal     = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    account_id   = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)

    product = db.relationship("StockProduct")
    uom     = db.relationship("StockUom")
    tax     = db.relationship("CoreTax")
    account = db.relationship("AccAccount")
