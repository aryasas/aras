from core import Aras
from .models import Report
from . import views # Trigger view registration
from .routers import router as report_router

from core.registry.config_registry import ConfigSection, ConfigField

class ReportApp(Aras.App):
    app_name = "report"
    app_label = "Reports"
    icon = "FileBarChart"

    config_sections = [
        ConfigSection(key="general", label="General", scope="module", fields=[
            ConfigField(key="default_date_range", type="choice", default="this_month", label="Default Date Range",
                        choices=[("today", "Today"), ("this_week", "This Week"), ("this_month", "This Month"),
                                 ("this_quarter", "This Quarter"), ("this_year", "This Year")]),
            ConfigField(key="export_format", type="choice", default="xlsx", label="Default Export Format",
                        choices=[("xlsx", "Excel"), ("csv", "CSV"), ("pdf", "PDF")]),
            ConfigField(key="row_limit", type="number", default=10000, label="Max Rows per Report"),
        ]),
        ConfigSection(key="scheduling", label="Scheduling", scope="module", fields=[
            ConfigField(key="enable_scheduled_reports", type="bool", default=False, label="Enable Scheduled Reports"),
            ConfigField(key="delivery_email", type="string", label="Default Delivery Email"),
        ]),
    ]

    routers = [report_router]
    models = [Report]

    menu_groups = [
        {
            "label": "All Reports",
            "icon": "FileText",
            "models": ["report_reports"]
        }
    ]

    @classmethod
    def seed(cls, db):
        from .seed_reports import run_seed as seed_reports
        from apps.config.models import Organization
        org = db.query(Organization).first()
        if org:
            seed_reports(db, org.id)
