from arasCore.lib.core.base_model import db
from arasCore.aras_gen import ArasModel, Col, String


class ModeOfPayment(ArasModel):
    __tablename__ = "erp_mode_of_payment"
    __app__       = "erp"
    __menu__      = "Settings"
    __title__     = "Mode of Payment"
    __icon__      = "fa-credit-card"
    __display_fields__ = ("name",)

    name         = String(null=False, unique=True, length=100, label="Name")
    payment_type = String(null=False, default="cash", length=20, label="Payment Type",
                          choices=["cash", "bank", "ewallet", "other"])

    company_accounts = db.relationship(
        "CompanyPaymentAccount", backref="mode_of_payment",
        cascade="all, delete-orphan", lazy="dynamic",
    )


class CompanyPaymentAccount(ArasModel):
    """Per-company COA account for each Mode of Payment — child table on ModeOfPayment form."""
    __tablename__ = "erp_company_payment_account"
    __app__       = "erp"
    __is_child__  = True
    __title__     = "Company Payment Account"

    mode_of_payment_id = Col(fk="erp_mode_of_payment.id", null=False, label="Mode of Payment")
    company_id         = Col(fk="company.id",             null=False, label="Company")
    account_id         = Col(fk="acc_account.id",         null=False, label="Account")

    company = db.relationship("Company", backref=db.backref("payment_accounts", lazy="dynamic"))
    account = db.relationship("AccAccount")

    __table_args__ = (
        db.UniqueConstraint("mode_of_payment_id", "company_id", name="uq_mop_company"),
    )
