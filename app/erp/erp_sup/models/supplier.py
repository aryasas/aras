from arasCore.arasgen import ArasGen
from app.erp.erp_sup.manifest import Sup
from arasCore.lib.core.base_model import ArasSoftModel, db


class SupSupplier(ArasGen.Model, module=Sup):
    __title__     = "Suppliers"
    __icon__      = "fa-truck"
    __menu_order__= 3
    __tablename__ = "sup_supplier"
    __display_fields__ = ("code", "name")
    __table_args__ = (
        db.UniqueConstraint("company_id", "code", name="uq_sup_supplier_code"),
        db.Index("idx_sup_supplier_name", "company_id", "name"),
    )

    company_id        = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=False)
    code              = db.Column(db.String(30), nullable=False)
    name              = db.Column(db.String(200), nullable=False)
    group_id          = db.Column(db.Integer, db.ForeignKey("sup_supplier_group.id"), nullable=True)
    email             = db.Column(db.String(120), nullable=True)
    phone             = db.Column(db.String(50), nullable=True)
    mobile            = db.Column(db.String(50), nullable=True)
    address           = db.Column(db.Text, nullable=True)
    city              = db.Column(db.String(100), nullable=True)
    country           = db.Column(db.String(100), nullable=True)
    tax_id            = db.Column(db.String(50), nullable=True)
    currency_id       = db.Column(db.Integer, db.ForeignKey("cfg_currency.id"), nullable=True)
    payment_term_days = db.Column(db.Integer, default=30)
    credit_limit      = db.Column(db.Numeric(18, 4), default=0)
    bank_name         = db.Column(db.String(100), nullable=True)
    bank_account_no   = db.Column(db.String(50), nullable=True)
    bank_account_name = db.Column(db.String(200), nullable=True)
    notes             = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<SupSupplier {self.code} {self.name}>"
