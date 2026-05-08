from arasCore.arasgen import ArasGen
from app.erp.erp_config.manifest import Config
from arasCore.lib.core.base_model import ArasModel, ArasSoftModel, db

class Charge(ArasGen.Model, module=Config):
    __title__     = "Charges"
    __icon__      = "fa-percent"
    __menu_order__= 0
    """Universal charge/tax/fee — percent or fixed amount, for sales/purchase/both."""
    __tablename__ = "cfg_charge"
    __display_fields__ = ("name",)

    company_id   = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=False)
    code         = db.Column(db.String(20), nullable=False)
    name         = db.Column(db.String(100), nullable=False)
    charge_type  = db.Column(db.String(20), default="both")    # sales/purchase/both
    calc_method  = db.Column(db.String(10), default="percent")  # percent/fixed
    rate         = db.Column(db.Numeric(9, 4), default=0)
    amount       = db.Column(db.Numeric(18, 4), default=0)
    is_inclusive = db.Column(db.Boolean, default=False)
    is_compound  = db.Column(db.Boolean, default=False)
    sequence     = db.Column(db.Integer, default=10)
    account_collected_id = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    account_paid_id      = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)

    account_collected = db.relationship("AccAccount", foreign_keys=[account_collected_id])
    account_paid      = db.relationship("AccAccount", foreign_keys=[account_paid_id])

    def __repr__(self):
        return f"<Charge {self.code}>"


class CompanyDefaultCharge(ArasGen.Model, module=Config):
    """Default charges auto-applied per company — shown as child table on Company form."""
    __tablename__ = "cfg_company_default_charge"

    company_id = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=False)
    charge_id  = db.Column(db.Integer, db.ForeignKey("cfg_charge.id"), nullable=False)
    apply_to   = db.Column(db.String(20), default="sales")  # sales/purchase/both/pos

    company = db.relationship("Company", backref=db.backref("default_charges", lazy="dynamic"))
    charge  = db.relationship("Charge")
