from arasCore.lib.base_model import ArasModel, db


class AccBankStatement(ArasModel):
    __tablename__ = "acc_bank_statement"

    company_id    = db.Column(db.Integer, db.ForeignKey("core_company.id"), nullable=False)
    journal_id    = db.Column(db.Integer, db.ForeignKey("acc_journal.id"), nullable=False)
    date_start    = db.Column(db.Date, nullable=False)
    date_end      = db.Column(db.Date, nullable=False)
    balance_start = db.Column(db.Numeric(18, 4), nullable=False, default=0)
    balance_end   = db.Column(db.Numeric(18, 4), nullable=False, default=0)
    state         = db.Column(db.Enum("draft", "reconciled", "closed"), default="draft", nullable=False)

    lines = db.relationship("AccBankStatementLine", backref="statement", cascade="all, delete-orphan")


class AccBankStatementLine(ArasModel):
    __tablename__ = "acc_bank_statement_line"

    statement_id            = db.Column(db.Integer, db.ForeignKey("acc_bank_statement.id"), nullable=False)
    date                    = db.Column(db.Date, nullable=False)
    amount                  = db.Column(db.Numeric(18, 4), nullable=False)
    partner_name_raw        = db.Column(db.String(200))
    reference               = db.Column(db.String(100))
    memo                    = db.Column(db.String(255))
    matched_payment_id      = db.Column(db.BigInteger, nullable=True)
    matched_journal_line_id = db.Column(db.BigInteger, db.ForeignKey("acc_journal_line.id"), nullable=True)
    state                   = db.Column(db.Enum("open", "matched", "manual"), default="open", nullable=False)
