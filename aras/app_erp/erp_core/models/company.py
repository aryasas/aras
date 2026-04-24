from arasCore.lib.base_model import ArasModel, db


class CoreCompany(ArasModel):
    __tablename__ = "core_company"
    __display_fields__ = ("code", "legal_name")

    code                    = db.Column(db.String(20), unique=True, nullable=False)
    legal_name              = db.Column(db.String(255), nullable=False)
    trade_name              = db.Column(db.String(255), nullable=True)
    tax_id                  = db.Column(db.String(50), nullable=True)
    address                 = db.Column(db.Text, nullable=True)
    phone                   = db.Column(db.String(50), nullable=True)
    email                   = db.Column(db.String(120), nullable=True)
    website                 = db.Column(db.String(255), nullable=True)
    logo_path               = db.Column(db.String(500), nullable=True)
    base_currency_id        = db.Column(db.Integer, db.ForeignKey("core_currency.id"), nullable=True)
    fiscal_year_start_month = db.Column(db.SmallInteger, default=1)
    default_tax_id          = db.Column(db.Integer, db.ForeignKey("core_tax.id"), nullable=True)
    default_coa_template    = db.Column(db.String(50), nullable=True)
    parent_id               = db.Column(db.Integer, db.ForeignKey("core_company.id"), nullable=True)

    branches = db.relationship("CoreCompanyBranch", backref="company", lazy="dynamic")
    parent   = db.relationship("CoreCompany", remote_side="CoreCompany.id", foreign_keys=[parent_id])

    def __repr__(self):
        return f"<CoreCompany {self.code}>"


class CoreCompanyBranch(ArasModel):
    __tablename__ = "core_company_branch"

    company_id = db.Column(db.Integer, db.ForeignKey("core_company.id"), nullable=False)
    code       = db.Column(db.String(20), nullable=False)
    name       = db.Column(db.String(200), nullable=False)
    address    = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<CoreCompanyBranch {self.code}>"
