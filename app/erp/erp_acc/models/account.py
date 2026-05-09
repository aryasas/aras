from enum import Enum
from arasCore.arasgen import ArasGen
from app.erp.erp_acc.manifest import Acc
from arasCore.lib.core.base_model import ArasModel, db

class AccountType(Enum):
    ASSET_CURRENT = "asset_current"
    ASSET_FIXED = "asset_fixed"
    ASSET_OTHER = "asset_other"
    LIABILITY_CURRENT = "liability_current"
    LIABILITY_LONG = "liability_long"
    EQUITY = "equity"
    INCOME_OPERATING = "income_operating"
    INCOME_OTHER = "income_other"
    EXPENSE_OPERATING = "expense_operating"
    EXPENSE_COGS = "expense_cogs"
    EXPENSE_OTHER = "expense_other"
    VIEW = "view"


class AccAccount(ArasGen.Model, module=Acc):
    __tablename__ = "acc_account"
    __table_args__ = (
        db.UniqueConstraint("company_id", "code", name="uq_acc_account_company_code"),
    )

    @classmethod
    def __fk_filter__(cls, q):
        """Exclude group accounts from FK dropdowns — only ledger accounts can be journaled."""
        return q.filter(cls.is_group == False)

    id              = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    company_id      = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=False)
    code            = db.Column(db.String(20), nullable=False)
    name            = db.Column(db.String(200), nullable=False)
    account_type    = db.Column(db.Enum(AccountType, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    parent_id       = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    is_group        = db.Column(db.Boolean, default=False, nullable=False)
    is_reconcilable = db.Column(db.Boolean, default=False, nullable=False)
    currency_id     = db.Column(db.Integer, db.ForeignKey("cfg_currency.id"), nullable=True)
    charge_id_default = db.Column(db.Integer, db.ForeignKey("cfg_charge.id"), nullable=True)
    allow_manual    = db.Column(db.Boolean, default=True, nullable=False)

    parent = db.relationship("AccAccount", remote_side=[id], backref="children")
