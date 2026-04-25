from arasCore.lib.base_model import ArasModel, ArasSoftModel, db


class ChargeCategory(ArasModel):
    __tablename__ = "charge_category"

    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    code       = db.Column(db.String(20), nullable=False)
    name       = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<ChargeCategory {self.code}>"


class Charge(ArasSoftModel):
    __tablename__ = "charge"
    __soft_delete__ = True

    company_id   = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    category_id  = db.Column(db.Integer, db.ForeignKey("charge_category.id"), nullable=True)
    code         = db.Column(db.String(20), nullable=False)
    name         = db.Column(db.String(100), nullable=False)
    charge_type  = db.Column(db.String(20), default="sales")   # sales/purchase/withholding/both
    calc_method  = db.Column(db.String(10), default="percent")  # percent/fixed
    rate         = db.Column(db.Numeric(9, 4), nullable=False, default=0)
    is_inclusive = db.Column(db.Boolean, default=False)
    is_compound  = db.Column(db.Boolean, default=False)
    sequence     = db.Column(db.Integer, default=10)
    account_collected_id = db.Column(db.Integer, nullable=True)
    account_paid_id      = db.Column(db.Integer, nullable=True)

    category = db.relationship("ChargeCategory")

    def __repr__(self):
        return f"<Charge {self.code} {self.rate}%>"
