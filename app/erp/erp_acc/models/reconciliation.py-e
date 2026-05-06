from arasCore.lib.base_model import ArasModel, db


class AccReconciliation(ArasModel):
    __tablename__ = "acc_reconciliation"

    company_id      = db.Column(db.Integer, db.ForeignKey("core_company.id"), nullable=False)
    account_id      = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=False)
    date_reconciled = db.Column(db.Date, nullable=False)
    total_amount    = db.Column(db.Numeric(18, 4), nullable=False)
    partner_id      = db.Column(db.BigInteger, nullable=True)
    partner_type    = db.Column(db.Enum("customer", "vendor", "employee", "none"), default="none")
