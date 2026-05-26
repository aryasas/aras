from core import Aras
from .models import Report
from . import views # Trigger view registration
from .routers import router as report_router

class ReportApp(Aras.App):
    app_name = "report"
    table_prefix = "erp_report"
    app_label = "Reports"
    icon = "FileBarChart"

    routers = [report_router]
    models = [Report]

    menu_groups = [
        {
            "label": "All Reports",
            "icon": "FileText",
            "models": ["erp_report_reports"]
        }
    ]

    @classmethod
    def seed(cls, db):
        from .seed_reports import run_seed as seed_reports
        from apps.config.models import Organization
        org = db.query(Organization).first()
        if org:
            seed_reports(db, org.id)
