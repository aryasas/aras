from arasCore.lib.base_model import ArasModel, ArasSoftModel, db


class CoreTax(ArasSoftModel):
    __tablename__ = "core_tax"
    __soft_delete__ = True

    company_id           = db.Column(db.Integer, db.ForeignKey("core_company.id"), nullable=False)
    code                 = db.Column(db.String(20), nullable=False)
    name                 = db.Column(db.String(100), nullable=False)
    tax_type             = db.Column(db.String(20), default="sales")   # sales/purchase/withholding/both
    calc_method          = db.Column(db.String(10), default="percent")  # percent/fixed
    rate                 = db.Column(db.Numeric(9, 4), nullable=False, default=0)
    is_inclusive         = db.Column(db.Boolean, default=False)
    is_compound          = db.Column(db.Boolean, default=False)
    sequence             = db.Column(db.Integer, default=10)
    account_collected_id = db.Column(db.Integer, nullable=True)
    account_paid_id      = db.Column(db.Integer, nullable=True)
    account_expense_id   = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f"<CoreTax {self.code} {self.rate}%>"


class CoreTaxGroup(ArasModel):
    __tablename__ = "core_tax_group"

    company_id = db.Column(db.Integer, db.ForeignKey("core_company.id"), nullable=False)
    code       = db.Column(db.String(20), nullable=False)
    name       = db.Column(db.String(100), nullable=False)

    lines = db.relationship("CoreTaxGroupLine", backref="group", lazy="dynamic",
                            cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CoreTaxGroup {self.code}>"


class CoreTaxGroupLine(ArasModel):
    __tablename__ = "core_tax_group_line"

    group_id = db.Column(db.Integer, db.ForeignKey("core_tax_group.id"), nullable=False)
    tax_id   = db.Column(db.Integer, db.ForeignKey("core_tax.id"), nullable=False)
    sequence = db.Column(db.Integer, default=10)

    tax = db.relationship("CoreTax")
