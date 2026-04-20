from datetime import datetime
from arasCore.lib.extensions import db


class ErpReport(db.Model):
    __tablename__ = "erp_report"

    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id   = db.Column(db.Integer, db.ForeignKey("core_company.id"), nullable=True)
    name         = db.Column(db.String(100), nullable=False, unique=True)
    title        = db.Column(db.String(200), nullable=False)
    module       = db.Column(db.String(50), nullable=False, default="general")
    report_type  = db.Column(db.Enum("query", "script", "jinja"), nullable=False, default="query")
    script       = db.Column(db.Text, nullable=True)
    columns_json = db.Column(db.Text, nullable=True)
    filters_json = db.Column(db.Text, nullable=True)
    is_active    = db.Column(db.Boolean, default=True, nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by   = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)

    favorites = db.relationship("ErpReportFavorite", backref="report", cascade="all, delete-orphan")


class ErpReportFavorite(db.Model):
    __tablename__ = "erp_report_favorite"
    __table_args__ = (
        db.UniqueConstraint("user_id", "report_id", name="uq_report_favorite"),
    )

    id        = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id   = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey("erp_report.id"), nullable=False)
