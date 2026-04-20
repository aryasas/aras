from arasCore.lib.base_model import ArasModel, db


class CoreFiscalYear(ArasModel):
    __tablename__ = "core_fiscal_year"

    company_id = db.Column(db.Integer, db.ForeignKey("core_company.id"), nullable=False)
    code       = db.Column(db.String(20), nullable=False)  # FY2026
    date_start = db.Column(db.Date, nullable=False)
    date_end   = db.Column(db.Date, nullable=False)
    state      = db.Column(db.String(10), default="open")  # open/locked/closed

    periods = db.relationship("CoreFiscalPeriod", backref="fiscal_year", lazy="dynamic",
                              cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CoreFiscalYear {self.code}>"


class CoreFiscalPeriod(ArasModel):
    __tablename__ = "core_fiscal_period"

    fiscal_year_id = db.Column(db.Integer, db.ForeignKey("core_fiscal_year.id"), nullable=False)
    code           = db.Column(db.String(10), nullable=False)  # 2026-04
    date_start     = db.Column(db.Date, nullable=False)
    date_end       = db.Column(db.Date, nullable=False)
    state          = db.Column(db.String(10), default="open")  # open/locked/closed

    def __repr__(self):
        return f"<CoreFiscalPeriod {self.code} [{self.state}]>"
