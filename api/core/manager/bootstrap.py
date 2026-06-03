"""
Seed admin user, default widgets, and default settings on first boot.
Called once from the FastAPI lifespan after sync completes.
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy import or_

logger = logging.getLogger(__name__)


def run(db: Session) -> None:
    """Idempotent: skips anything that already exists."""
    _seed_admin(db)
    _seed_widgets(db)
    _seed_settings(db)
    _seed_i18n(db)
    _seed_framework_rbac(db)
    _run_app_seeds(db)
    _seed_saas_plans(db)
    _seed_reports(db)


def _seed_admin(db: Session) -> None:
    from core.auth.models import User
    from core.lib.settings import settings

    if db.query(User).filter(User.username == "admin").first():
        return
    logger.info("Creating default admin user...")
    db.add(User(
        username="admin",
        email="admin@aras.local",
        password_hash=User.hash_password(settings.ARAS_ADMIN_PASSWORD),
        is_admin=True,
    ))
    db.commit()
    logger.info("Admin user created.")


def _seed_widgets(db: Session) -> None:
    from core.registry.widget_model import WidgetModel

    if db.query(WidgetModel).first():
        return
    logger.info("Seeding default widgets...")
    db.add_all([
        WidgetModel(
            name="total_users", title="Total Users", widget_type="stat",
            resource_name="core_users",
            config_json={"icon": "Users", "color": "indigo"}, order=1,
        ),
        WidgetModel(
            name="recent_activity", title="Recent Activity", widget_type="list",
            resource_name="core_activity_logs",
            config_json={"limit": 5}, order=2, size="col-span-2",
        ),
        WidgetModel(
            name="active_apps", title="Installed Apps", widget_type="stat",
            resource_name="core_apps",
            config_json={"icon": "Package", "color": "emerald"}, order=3,
        ),
    ])
    db.commit()
    logger.info("Default widgets seeded.")


def _seed_settings(db: Session) -> None:
    from core.aras import Aras
    from core.lib.settings import settings

    defaults = [
        {"namespace": "core", "key": "app_name",              "value": settings.APP_NAME,  "description": "Application display name"},
        {"namespace": "core", "key": "maintenance_mode",      "value": "false",             "description": "Disable public access"},
        {"namespace": "core", "key": "default_language",      "value": "en",                "description": "System-wide default language"},
        {"namespace": "core", "key": "date_format",           "value": "YYYY-MM-DD",        "description": "Global date format"},
        {"namespace": "core", "key": "number_format",         "value": "#,###.##",          "description": "Global number format"},
        {"namespace": "core", "key": "decimal_precision",     "value": "2",                 "description": "Global decimal precision"},
        {"namespace": "core", "key": "currency_symbol",       "value": "$",                 "description": "Global currency symbol"},
        {"namespace": "core", "key": "language_default",      "value": "en",                "description": "Global default language"},
    ]
    
    for d in defaults:
        existing = db.query(Aras.SettingsModel).filter_by(namespace=d["namespace"], key=d["key"]).first()
        if not existing:
            db.add(Aras.SettingsModel(**d))
            
    db.commit()
    logger.info("Default settings seeded.")


def _seed_framework_rbac(db: Session) -> None:
    from pathlib import Path
    from core.seeds.loader import load_rbac
    seed_file = Path(__file__).parent.parent / "seeds" / "rbac_framework.yaml"
    load_rbac(seed_file, db)


def _seed_i18n(db: Session) -> None:
    from core.lib.i18n import seed_locale_translations
    result = seed_locale_translations(db)
    logger.info(
        "Locale translations seeded: inserted=%d updated=%d skipped=%d",
        result["inserted"],
        result["updated"],
        result["skipped"],
    )


def _run_app_seeds(db: Session) -> None:
    # Import app seed modules so their @register decorators fire before run_all.
    # Add new app seeds here as: try: import apps.<name>.seed_rbac; except ImportError: pass
    try:
        import apps.config.seed_rbac  # noqa: F401
    except ImportError:
        pass
    from core.seeds import registry
    registry.run_all(db)


def _seed_saas_plans(db: Session) -> None:
    try:
        from apps.saas.plans import seed_default_plans
        seed_default_plans(db)
    except ImportError:
        pass


def _seed_reports(db: Session) -> None:
    # claude-sonnet-4-6
    try:
        from apps.report.seed_reports import run_seed
        from apps.config.models import Organization

        from apps.report.models import Report
        deleted = db.query(Report).filter(or_(Report.code.is_(None), Report.code == '')).delete()
        if deleted:
            db.commit()
            logger.info(f"Removed {deleted} orphaned report(s) with no code.")

        orgs = db.query(Organization).all()
        if not orgs:
            logger.info("Creating default organization for reports...")
            org = Organization(name="Default", code="default")
            db.add(org)
            db.commit()
            orgs = [org]
        for org in orgs:
            logger.info(f"Seeding reports for org {org.id}...")
            run_seed(db, org.id)
        logger.info("Reports seeded successfully.")
    except (ImportError, Exception) as e:
        logger.error(f"Report seeding failed: {e}", exc_info=True)
