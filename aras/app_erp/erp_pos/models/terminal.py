from datetime import datetime
from arasCore.lib.base_model import ArasModel, db


class PosTerminal(ArasModel):
    __tablename__ = "pos_terminal"
    __table_args__ = (
        db.UniqueConstraint("company_id", "code", name="uq_pos_terminal_code"),
    )

    company_id        = db.Column(db.Integer, db.ForeignKey("core_company.id"), nullable=False)
    branch_id         = db.Column(db.Integer, db.ForeignKey("core_company_branch.id"), nullable=True)
    code              = db.Column(db.String(20), nullable=False)
    name              = db.Column(db.String(100), nullable=False)
    journal_id        = db.Column(db.Integer, db.ForeignKey("acc_journal.id"), nullable=True)
    sequence_id       = db.Column(db.Integer, db.ForeignKey("core_sequence.id"), nullable=True)
    warehouse_id      = db.Column(db.Integer, db.ForeignKey("stock_warehouse.id"), nullable=True)
    pricelist_id      = db.Column(db.Integer, db.ForeignKey("stock_price_list.id"), nullable=True)
    transaction_mode  = db.Column(db.Enum("income", "outcome", "both"), nullable=False, default="income")
    default_tax_id    = db.Column(db.Integer, db.ForeignKey("core_tax.id"), nullable=True)
    receipt_header    = db.Column(db.Text, nullable=True)
    receipt_footer    = db.Column(db.Text, nullable=True)
    allow_discount    = db.Column(db.Boolean, default=True)
    max_discount_pct  = db.Column(db.Numeric(5, 2), default=100)

    warehouse  = db.relationship("StockWarehouse", foreign_keys=[warehouse_id])
    pricelist  = db.relationship("StockPriceList", foreign_keys=[pricelist_id])
    sessions   = db.relationship("PosSession", backref="terminal", lazy="dynamic")

    def __repr__(self):
        return f"<PosTerminal {self.code}>"


class PosSession(ArasModel):
    __tablename__ = "pos_session"
    __table_args__ = (
        db.Index("idx_pos_session_terminal", "terminal_id", "state"),
    )

    terminal_id     = db.Column(db.Integer, db.ForeignKey("pos_terminal.id"), nullable=False)
    cashier_id      = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    shift_number    = db.Column(db.String(30), nullable=True)
    opening_balance = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    closing_balance = db.Column(db.Numeric(18, 4), nullable=True)
    cash_counted    = db.Column(db.Numeric(18, 4), nullable=True)
    cash_difference = db.Column(db.Numeric(18, 4), nullable=True)
    state           = db.Column(db.Enum("open", "closing", "closed"), default="open", nullable=False)
    opened_at       = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at       = db.Column(db.DateTime, nullable=True)
    notes           = db.Column(db.Text, nullable=True)

    cashier = db.relationship("User", foreign_keys=[cashier_id])
    orders  = db.relationship("PosOrder", backref="session", lazy="dynamic")

    def __repr__(self):
        return f"<PosSession terminal={self.terminal_id} [{self.state}]>"
