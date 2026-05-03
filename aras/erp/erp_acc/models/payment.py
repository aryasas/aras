from arasCore.lib.core.base_model import ArasModel, db


class AccPayment(ArasModel):
    """
    Single payment document covering one or more invoices.
    payment_type="inbound" = customer pays us (AR).
    payment_type="outbound" = we pay supplier (AP).
    """
    __tablename__ = "acc_payment"
    __table_args__ = (
        db.Index("ix_acc_pay_company_date", "company_id", "payment_date"),
        db.Index("ix_acc_pay_partner", "partner_type", "partner_id"),
    )

    id                 = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    company_id         = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    name               = db.Column(db.String(50), nullable=False)
    payment_type       = db.Column(db.Enum("inbound", "outbound"), nullable=False)
    partner_type       = db.Column(db.Enum("customer", "supplier", "other"), nullable=False, default="customer")
    partner_id         = db.Column(db.BigInteger, nullable=True)
    payment_date       = db.Column(db.Date, nullable=False)
    method             = db.Column(db.String(50), nullable=False, default="cash")
    mode_of_payment_id = db.Column(db.Integer, db.ForeignKey("erp_mode_of_payment.id"), nullable=True)
    total_amount       = db.Column(db.Numeric(18, 4), nullable=False)
    allocated_amount   = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    state              = db.Column(db.Enum("draft", "posted", "cancelled"), default="draft", nullable=False)
    reference          = db.Column(db.String(100), nullable=True)
    notes              = db.Column(db.Text, nullable=True)
    journal_entry_id   = db.Column(db.BigInteger, db.ForeignKey("acc_journal_entry.id"), nullable=True)

    mode_of_payment = db.relationship("ModeOfPayment")
    journal_entry   = db.relationship("AccJournalEntry")
    allocations     = db.relationship("AccPaymentAllocation", backref="payment",
                                      cascade="all, delete-orphan")

    @property
    def unallocated_amount(self):
        return max(0.0, float(self.total_amount) - float(self.allocated_amount))

    def __repr__(self):
        return f"<AccPayment {self.name} [{self.state}]>"


class AccPaymentAllocation(ArasModel):
    """Links one payment to one invoice (sales or purchase) with a specific amount."""
    __tablename__ = "acc_payment_allocation"

    id           = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    payment_id   = db.Column(db.BigInteger, db.ForeignKey("acc_payment.id"), nullable=False)
    invoice_type = db.Column(db.Enum("sales", "purchase"), nullable=False)
    invoice_id   = db.Column(db.BigInteger, nullable=False)
    amount       = db.Column(db.Numeric(18, 4), nullable=False)
    notes        = db.Column(db.String(255), nullable=True)

    @property
    def invoice(self):
        if self.invoice_type == "sales":
            from aras.erp.erp_acc.models.invoice import AccSalesInvoice
            return AccSalesInvoice.get(self.invoice_id)
        from aras.erp.erp_acc.models.invoice import AccPurchaseInvoice
        return AccPurchaseInvoice.get(self.invoice_id)
