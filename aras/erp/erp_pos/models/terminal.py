from datetime import datetime
from arasCore.lib.core.base_model import ArasModel, db


class PosTerminal(ArasModel):
    __tablename__ = "pos_terminal"
    __table_args__ = (
        db.UniqueConstraint("company_id", "code", name="uq_pos_terminal_code"),
    )

    company_id          = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    code                = db.Column(db.String(20), nullable=False)
    name                = db.Column(db.String(100), nullable=False)
    sequence_id         = db.Column(db.Integer, db.ForeignKey("sequence.id"), nullable=True)
    invoice_sequence_id = db.Column(db.Integer, db.ForeignKey("sequence.id"), nullable=True)
    location_id         = db.Column(db.Integer, db.ForeignKey("stock_location.id"), nullable=True)
    selling_pricelist_id  = db.Column(db.Integer, db.ForeignKey("stock_price_list.id"), nullable=True)
    purchase_pricelist_id = db.Column(db.Integer, db.ForeignKey("stock_price_list.id"), nullable=True)
    transaction_mode    = db.Column(db.Enum("income", "outcome", "both"), nullable=False, default="income")
    default_tax_id      = db.Column(db.Integer, db.ForeignKey("charge.id"), nullable=True)
    receipt_header      = db.Column(db.Text, nullable=True)
    receipt_footer      = db.Column(db.Text, nullable=True)
    print_template_id   = db.Column(db.Integer, db.ForeignKey("print_template.id"), nullable=True)
    allow_discount      = db.Column(db.Boolean, default=True)
    max_discount_pct    = db.Column(db.Numeric(5, 2), default=100)

    # FK dropdown choices: filter by price_type so each field shows only relevant pricelists
    __fk_choices__ = {
        "selling_pricelist_id":  lambda q: q.filter_by(price_type="sales"),
        "purchase_pricelist_id": lambda q: q.filter_by(price_type="purchase"),
    }

    location           = db.relationship("StockLocation", foreign_keys=[location_id])
    selling_pricelist  = db.relationship("StockPriceList", foreign_keys=[selling_pricelist_id])
    purchase_pricelist = db.relationship("StockPriceList", foreign_keys=[purchase_pricelist_id])
    print_template = db.relationship("PrintTemplate", foreign_keys=[print_template_id])
    sessions       = db.relationship("PosSession", backref="terminal", lazy="dynamic")

    def __repr__(self):
        return f"<PosTerminal {self.code}>"


class PosSession(ArasModel):
    __tablename__ = "pos_session"
    __table_args__ = (
        db.Index("idx_pos_session_terminal", "terminal_id", "state"),
    )

    company_id      = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    terminal_id     = db.Column(db.Integer, db.ForeignKey("pos_terminal.id"), nullable=False)
    cashier_id      = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    shift_number    = db.Column(db.String(30), nullable=True)
    opening_balance = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    closing_balance = db.Column(db.Numeric(18, 4), nullable=True)
    cash_counted    = db.Column(db.Numeric(18, 4), nullable=True)
    # system-computed: cash_counted - expected_cash; read-only in UI
    cash_difference = db.Column(db.Numeric(18, 4), nullable=True)
    state           = db.Column(db.Enum("open", "closing", "closed"), default="open", nullable=False)
    opened_at       = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at       = db.Column(db.DateTime, nullable=True)
    notes           = db.Column(db.Text, nullable=True)

    cashier  = db.relationship("User", foreign_keys=[cashier_id])
    entries  = db.relationship("PosShiftEntry", backref="session", lazy="dynamic",
                              cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PosSession terminal={self.terminal_id} [{self.state}]>"


class PosShiftEntry(ArasModel):
    """Cash-in / cash-out entries within a shift (opening float, petty cash, etc.)."""
    __tablename__ = "pos_shift_entry"

    session_id       = db.Column(db.Integer, db.ForeignKey("pos_session.id"), nullable=False)
    entry_type       = db.Column(db.Enum("opening", "closing", "cash_in", "cash_out"), nullable=False)
    amount           = db.Column(db.Numeric(18, 4), nullable=False, default=0)
    note             = db.Column(db.String(255), nullable=True)
    journal_entry_id = db.Column(db.BigInteger, db.ForeignKey("acc_journal_entry.id"), nullable=True)
    entered_at       = db.Column(db.DateTime, default=datetime.utcnow)
    entered_by_id    = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)

    entered_by    = db.relationship("User", foreign_keys=[entered_by_id])
    journal_entry = db.relationship("AccJournalEntry", foreign_keys=[journal_entry_id])

    def __repr__(self):
        return f"<PosShiftEntry {self.entry_type} {self.amount}>"


class PosShiftBalance(ArasModel):
    """Per-MOP opening/closing balance for a shift — auto expected vs manual count."""
    __tablename__ = "pos_shift_balance"

    __table_args__ = (
        db.UniqueConstraint("session_id", "mode_of_payment_id", name="uq_shift_balance_mop"),
    )

    session_id         = db.Column(db.Integer, db.ForeignKey("pos_session.id"), nullable=False)
    mode_of_payment_id = db.Column(db.Integer, db.ForeignKey("erp_mode_of_payment.id"), nullable=False)
    opening_balance    = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    closing_balance    = db.Column(db.Numeric(18, 4), default=0, nullable=False)

    session         = db.relationship("PosSession", backref=db.backref("shift_balances", lazy="dynamic"))
    # mode_of_payment resolved via query

    def __repr__(self):
        return f"<PosShiftBalance session={self.session_id} mop={self.mode_of_payment_id}>"
