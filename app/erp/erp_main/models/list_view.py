from arasCore.arasgen import ArasGen
from app.erp.erp_main.manifest import Main
from arasCore.lib.core.base_model import ArasModel, db
from arasCore.admin.models import ListViewSetting as ErpListViewSetting  # noqa: F401


class ErpReportSetting(ArasGen.Model, module=Main):
    """Per-user saved defaults for a specific report (date preset, params, per_page)."""
    __tablename__ = "main_report_setting"
    __table_args__ = (
        db.UniqueConstraint("user_id", "report_id", name="uq_report_setting"),
    )

    user_id      = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    report_id    = db.Column(db.Integer, db.ForeignKey("main_report.id"), nullable=False)
    date_preset  = db.Column(db.String(20), default="this_month", nullable=False)
    date_from    = db.Column(db.String(20), nullable=True)
    date_to      = db.Column(db.String(20), nullable=True)
    params_json  = db.Column(db.Text, nullable=True)
    per_page     = db.Column(db.Integer, default=50, nullable=False)
