from arasCore.lib.base_model import ArasModel, db


class FiscalYear(ArasModel):
    __tablename__ = "fiscal_year"

    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    code       = db.Column(db.String(20), nullable=False)  # FY2026
    date_start = db.Column(db.Date, nullable=False)
    date_end   = db.Column(db.Date, nullable=False)
    state      = db.Column(db.String(10), default="open")  # open/locked/closed

    periods = db.relationship("FiscalPeriod", backref="fiscal_year", lazy="dynamic",
                              cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FiscalYear {self.code}>"


class FiscalPeriod(ArasModel):
    __tablename__ = "fiscal_period"

    fiscal_year_id = db.Column(db.Integer, db.ForeignKey("fiscal_year.id"), nullable=False)
    code           = db.Column(db.String(10), nullable=False)  # 2026-04
    date_start     = db.Column(db.Date, nullable=False)
    date_end       = db.Column(db.Date, nullable=False)
    state          = db.Column(db.String(10), default="open")  # open/locked/closed

    def __repr__(self):
        return f"<FiscalPeriod {self.code} [{self.state}]>"
