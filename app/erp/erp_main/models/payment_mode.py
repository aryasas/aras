from arasCore.arasgen import ArasGen
from app.erp.erp_main.manifest import Main
from arasCore.lib.core.base_model import db


class ModeOfPayment(ArasGen.Model, module=Main):
    __tablename__ = "main_mode_of_payment"
    __title__     = "Mode of Payment"
    __icon__      = "fa-credit-card"
    __menu_order__= 0
    __display_fields__ = ("name",)

    name         = ArasGen.String(null=False, unique=True, length=100, label="Name")
    payment_type = ArasGen.String(null=False, default="cash", length=20, label="Payment Type",
                          choices=["cash", "bank", "ewallet", "other"])

    company_accounts = db.relationship(
        "CompanyPaymentAccount", backref="mode_of_payment",
        cascade="all, delete-orphan", lazy="dynamic",
    )


class CompanyPaymentAccount(ArasGen.Model, module=Main):
    """Per-company COA account for each Mode of Payment — child table on ModeOfPayment form."""
    __tablename__ = "main_company_payment_account"
    __is_child__  = True
    __title__     = "Company Payment Account"

    mode_of_payment_id = ArasGen.Col(fk="main_mode_of_payment.id", null=False, label="Mode of Payment")
    company_id         = ArasGen.Col(fk="cfg_company.id",             null=False, label="Company")
    account_id         = ArasGen.Col(fk="acc_account.id",         null=False, label="Account")

    company = db.relationship("Company", backref=db.backref("payment_accounts", lazy="dynamic"))
    account = db.relationship("AccAccount")

    __table_args__ = (
        db.UniqueConstraint("mode_of_payment_id", "company_id", name="uq_mop_company"),
    )
