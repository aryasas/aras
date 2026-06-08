from core import Aras
from .models import Report
from . import views # Trigger view registration
from .routers import router as report_router

from core.registry.config_registry import ConfigSection, ConfigField

# claude-opus-4-8
# Inverted hook: report seeding on org creation. Lives app-side (not in the
# framework Organization model) to keep core free of apps/* imports.
from sqlalchemy import event
from core.workspace.models import Organization

@event.listens_for(Organization, "after_insert")
def _seed_reports_for_new_org(mapper, connection, target):
    db = getattr(target, "db_session", None)
    if db is None:
        return
    try:
        from core.report.seed_reports import run_seed
        run_seed(db, target.id)
    except Exception:
        pass

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
        # Self-contained report seeding. Cleans orphan reports and seeds 
        # reports for every EXISTING organization.
        import logging
        from sqlalchemy import or_
        from .seed_reports import run_seed as seed_reports
        from .models import Report
        from core.workspace.models import Organization
        log = logging.getLogger(__name__)
        try:
            deleted = db.query(Report).filter(or_(Report.code.is_(None), Report.code == "")).delete()
            if deleted:
                db.commit()
                log.info("Removed %d orphaned report(s) with no code.", deleted)

            orgs = db.query(Organization).all()
            for org in orgs:
                seed_reports(db, org.id)
            db.commit()
        except Exception as e:
            db.rollback()
            log.error("Report seeding failed: %s", e, exc_info=True)
