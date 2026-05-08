from arasCore.arasgen import ArasGen
from app.erp.erp_main.manifest import Main
from arasCore.lib.core.base_model import ArasModel, db


class ErpReport(ArasGen.Model, module=Main):
    __title__     = "Report Templates"
    __menu__      = "Reports"
    __icon__      = "fa-file-text-o"
    __menu_order__= 5
    __tablename__ = "main_report"

    company_id   = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=True)
    name         = db.Column(db.String(100), nullable=False, unique=True)
    title        = db.Column(db.String(200), nullable=False)
    module       = db.Column(db.String(50), nullable=False, default="general")
    report_type  = db.Column(db.Enum("query", "script", "jinja"), nullable=False, default="query")
    # "list" = render as searchable/filterable list (ab_list style)
    # "custom" = render with formula/script view (filters + run button)
    render_mode  = db.Column(db.Enum("list", "custom"), nullable=False, default="list")
    script       = db.Column(db.Text, nullable=True)
    columns_json = db.Column(db.Text, nullable=True)
    filters_json = db.Column(db.Text, nullable=True)

    favorites = db.relationship("ErpReportFavorite", back_populates="report", cascade="all, delete-orphan")


class ErpReportFavorite(ArasGen.Model, module=Main):
    __tablename__ = "main_report_favorite"
    __table_args__ = (
        db.UniqueConstraint("user_id", "report_id", name="uq_report_favorite"),
    )

    user_id   = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey("main_report.id"), nullable=False)

    report = db.relationship("ErpReport", back_populates="favorites")
