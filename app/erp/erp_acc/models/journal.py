from arasCore.arasgen import ArasGen
from app.erp.erp_acc.manifest import Acc
from arasCore.lib.core.base_model import ArasModel, db


class AccJournalEntry(ArasGen.Model, module=Acc):
    __title__     = "Journal Entries"
    __icon__      = "fa-pencil-square-o"
    __url__       = "acc/entry"
    __menu_order__= 1
    __tablename__ = "acc_journal_entry"
    __table_args__ = (
        db.Index("ix_acc_je_company_date", "company_id", "date_entry"),
        db.Index("ix_acc_je_origin", "origin_model", "origin_id"),
    )

    id               = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    company_id       = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=False)
    name             = db.Column(db.String(50), nullable=False)
    date_entry       = db.Column(db.Date, nullable=False)
    reference        = db.Column(db.String(100))
    narrative        = db.Column(db.Text)
    state            = db.Column(db.Enum("draft", "posted", "cancelled"), nullable=False, default="draft")
    origin_model     = db.Column(db.String(50))
    origin_id        = db.Column(db.BigInteger)
    fiscal_period_id = db.Column(db.Integer, db.ForeignKey("main_fiscal_period.id"), nullable=True)
    amount_total     = db.Column(db.Numeric(18, 4), default=0)
    posted_at        = db.Column(db.DateTime)
    posted_by        = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)

    lines = db.relationship("AccJournalLine", backref="entry", cascade="all, delete-orphan")

    def before_delete(self, user_id=None):
        # Null out FK on stock_movement before deleting to avoid FK constraint errors
        db.session.execute(
            db.text("UPDATE stock_movement SET journal_entry_id=NULL WHERE journal_entry_id=:id"),
            {"id": self.id},
        )
        db.session.flush()

    def list(self, query):
        return query.filter_by(state="draft")

class AccJournalLine(ArasGen.Model, module=Acc):
    __is_child__  = True
    __url__       = "acc/line"
    __tablename__ = "acc_journal_line"
    __table_args__ = (
        db.Index("ix_acc_jl_account_entry", "account_id", "entry_id"),
        db.Index("ix_acc_jl_partner", "partner_type", "partner_id"),
    )

    id              = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    entry_id        = db.Column(db.BigInteger, db.ForeignKey("acc_journal_entry.id"), nullable=False)
    sequence        = db.Column(db.Integer, default=0)
    account_id      = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=False)
    partner_type    = db.Column(db.Enum("customer", "vendor", "employee", "none"), default="none", nullable=False)
    partner_id      = db.Column(db.BigInteger, nullable=True)
    debit           = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    credit          = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    currency_id     = db.Column(db.Integer, db.ForeignKey("cfg_currency.id"), nullable=True)
    amount_currency = db.Column(db.Numeric(18, 4), nullable=True)
    fx_rate         = db.Column(db.Numeric(18, 6), nullable=True)
    charge_id       = db.Column(db.Integer, db.ForeignKey("cfg_charge.id"), nullable=True)
    tax_base_amount = db.Column(db.Numeric(18, 4), nullable=True)
    analytic_tag_id = db.Column(db.Integer, db.ForeignKey("acc_analytic_tag.id"), nullable=True)
    description     = db.Column(db.String(255))

    account = db.relationship("AccAccount")
