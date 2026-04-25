from arasCore.lib.base_model import ArasModel, db


class AccSalesInvoice(ArasModel):
    __tablename__ = "acc_sales_invoice"
    __table_args__ = (
        db.Index("ix_sal_inv_company_date", "company_id", "invoice_date"),
        db.Index("ix_sal_inv_customer", "customer_id"),
        db.Index("ix_sal_inv_state", "state"),
    )

    id                = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    company_id        = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    name              = db.Column(db.String(50), nullable=False)
    customer_id       = db.Column(db.Integer, db.ForeignKey("crm_customer.id"), nullable=False)
    invoice_date      = db.Column(db.Date, nullable=False)
    due_date          = db.Column(db.Date, nullable=True)
    currency_id       = db.Column(db.Integer, db.ForeignKey("currency.id"), nullable=False)
    fiscal_period_id  = db.Column(db.Integer, db.ForeignKey("fiscal_period.id"), nullable=True)
    subtotal          = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    discount_amt      = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    charge_amt        = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    total             = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    amount_paid       = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    amount_due        = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    state             = db.Column(db.Enum("draft", "posted", "partial", "paid", "cancelled"),
                                  default="draft", nullable=False)
    payment_term_days = db.Column(db.Integer, default=0)
    reference         = db.Column(db.String(100), nullable=True)
    notes             = db.Column(db.Text, nullable=True)
    journal_entry_id  = db.Column(db.BigInteger, db.ForeignKey("acc_journal_entry.id"), nullable=True)
    pos_order_id      = db.Column(db.BigInteger, db.ForeignKey("pos_order.id"), nullable=True)

    company       = db.relationship("Company")
    customer      = db.relationship("CrmCustomer")
    currency      = db.relationship("Currency")
    journal_entry = db.relationship("AccJournalEntry")
    lines         = db.relationship("AccSalesInvoiceLine", backref="invoice",
                                    cascade="all, delete-orphan")
    charges       = db.relationship("AccSalesInvoiceCharge", backref="invoice",
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
    __table_args__ = (
        db.Index("ix_pur_inv_company_date", "company_id", "invoice_date"),
        db.Index("ix_pur_inv_state", "state"),
    )

    id                = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    company_id        = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    name              = db.Column(db.String(50), nullable=False)
    vendor_name       = db.Column(db.String(200), nullable=False)
    vendor_ref        = db.Column(db.String(100), nullable=True)
    invoice_date      = db.Column(db.Date, nullable=False)
    due_date          = db.Column(db.Date, nullable=True)
    currency_id       = db.Column(db.Integer, db.ForeignKey("currency.id"), nullable=False)
    fiscal_period_id  = db.Column(db.Integer, db.ForeignKey("fiscal_period.id"), nullable=True)
    subtotal          = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    discount_amt      = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    charge_amt        = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    total             = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    amount_paid       = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    amount_due        = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    state             = db.Column(db.Enum("draft", "posted", "partial", "paid", "cancelled"),
                                  default="draft", nullable=False)
    payment_term_days = db.Column(db.Integer, default=0)
    notes             = db.Column(db.Text, nullable=True)
    journal_entry_id  = db.Column(db.BigInteger, db.ForeignKey("acc_journal_entry.id"), nullable=True)
    pos_order_id      = db.Column(db.BigInteger, db.ForeignKey("pos_order.id"), nullable=True)

    company       = db.relationship("Company")
    currency      = db.relationship("Currency")
    journal_entry = db.relationship("AccJournalEntry")
    lines         = db.relationship("AccPurchaseInvoiceLine", backref="invoice",
                                    cascade="all, delete-orphan")
    charges       = db.relationship("AccPurchaseInvoiceCharge", backref="invoice",
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
