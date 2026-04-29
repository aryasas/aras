from arasCore.lib.core.base_model import ArasModel, db


class ModeOfPayment(ArasModel):
    __tablename__ = "erp_mode_of_payment"
    __display_fields__ = ("name",)

    name         = db.Column(db.String(100), nullable=False, unique=True)
    payment_type = db.Column(db.String(20), nullable=False, default="cash")  # cash/bank/ewallet/other

    company_accounts = db.relationship("CompanyPaymentAccount", backref="mode_of_payment",
                                       cascade="all, delete-orphan", lazy="dynamic")


class CompanyPaymentAccount(ArasModel):
    """Per-company COA account for each Mode of Payment — child table on ModeOfPayment form."""
    __tablename__ = "erp_company_payment_account"

    mode_of_payment_id = db.Column(db.Integer, db.ForeignKey("erp_mode_of_payment.id"), nullable=False)
    company_id         = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    account_id         = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=False)

    company = db.relationship("Company", backref=db.backref("payment_accounts", lazy="dynamic"))
    account = db.relationship("AccAccount")

    __table_args__ = (
        db.UniqueConstraint("mode_of_payment_id", "company_id", name="uq_mop_company"),
    )
