from arasCore.lib.base_model import ArasModel, db

ACCOUNT_TYPES = [
    "asset_current", "asset_fixed", "asset_other",
    "liability_current", "liability_long", "equity",
    "income_operating", "income_other",
    "expense_operating", "expense_cogs", "expense_other",
    "view",
]


class AccAccount(ArasModel):
    __tablename__ = "acc_account"
    __table_args__ = (
        db.UniqueConstraint("company_id", "code", name="uq_acc_account_company_code"),
    )

    id              = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    company_id      = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    code            = db.Column(db.String(20), nullable=False)
    name            = db.Column(db.String(200), nullable=False)
    account_type    = db.Column(db.Enum(*ACCOUNT_TYPES), nullable=False)
    parent_id       = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    is_group        = db.Column(db.Boolean, default=False, nullable=False)
    is_reconcilable = db.Column(db.Boolean, default=False, nullable=False)
    currency_id     = db.Column(db.Integer, db.ForeignKey("currency.id"), nullable=True)
    charge_id_default = db.Column(db.Integer, db.ForeignKey("charge.id"), nullable=True)
    allow_manual    = db.Column(db.Boolean, default=True, nullable=False)

    children = db.relationship("AccAccount", backref=db.backref("parent", remote_side=[id]))


class AccAnalyticTag(ArasModel):
    __tablename__ = "acc_analytic_tag"

    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    code       = db.Column(db.String(20), nullable=False)
    name       = db.Column(db.String(100), nullable=False)
    parent_id  = db.Column(db.Integer, db.ForeignKey("acc_analytic_tag.id"), nullable=True)
    type       = db.Column(db.Enum("cost_center", "project", "department", "custom"),
                           nullable=False, default="custom")
