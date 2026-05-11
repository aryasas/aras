from arasCore.arasgen import ArasGen
from app.erp.erp_main.manifest import Main
from arasCore.lib.core.base_model import ArasModel, db


class FiscalYear(ArasGen.Model, module=Main):
    __title__     = "Fiscal Year"
    __icon__      = "fa-calendar"
    __menu_order__= 0
    __tablename__ = "main_fiscal_year"

    company_id = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=False)
    code       = db.Column(db.String(20), nullable=False)  # FY2026
    date_start = db.Column(db.Date, nullable=False)
    date_end   = db.Column(db.Date, nullable=False)
    state      = db.Column(db.String(10), default="open")  # open/locked/closed

    periods = db.relationship("FiscalPeriod", back_populates="fiscal_year", lazy="dynamic",
                              cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FiscalYear {self.code}>"


class FiscalPeriod(ArasGen.Model, module=Main):
    __is_child__  = True
    __tablename__ = "main_fiscal_period"

    fiscal_year_id = db.Column(db.Integer, db.ForeignKey("main_fiscal_year.id"), nullable=False)
    code           = db.Column(db.String(10), nullable=False)  # 2026-04
    date_start     = db.Column(db.Date, nullable=False)
    date_end       = db.Column(db.Date, nullable=False)
    state          = db.Column(db.String(10), default="open")  # open/locked/closed

    fiscal_year = db.relationship("FiscalYear", back_populates="periods")

    def __repr__(self):
        return f"<FiscalPeriod {self.code} [{self.state}]>"
