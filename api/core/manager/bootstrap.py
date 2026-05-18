"""
Seed admin user, default widgets, and default settings on first boot.
Called once from the FastAPI lifespan after sync completes.
"""
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def run(db: Session) -> None:
    """Idempotent: skips anything that already exists."""
    _seed_admin(db)
    _seed_widgets(db)
    _seed_settings(db)
    _seed_erp_rbac(db)


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
            resource_name="auth_users",
            config_json={"icon": "Users", "color": "indigo"}, order=1,
        ),
        WidgetModel(
            name="recent_activity", title="Recent Activity", widget_type="list",
            resource_name="aras_activity_logs",
            config_json={"limit": 5}, order=2, size="col-span-2",
        ),
        WidgetModel(
            name="active_apps", title="Installed Apps", widget_type="stat",
            resource_name="aras_apps",
            config_json={"icon": "Package", "color": "emerald"}, order=3,
        ),
    ])
    db.commit()
    logger.info("Default widgets seeded.")


def _seed_settings(db: Session) -> None:
    from core.registry.sys_settings import ArasSetting
    from core.lib.settings import settings

    defaults = [
        {"key": "app_name",              "value": settings.APP_NAME,  "description": "Application display name"},
        {"key": "maintenance_mode",      "value": "false",             "description": "Disable public access"},
        {"key": "default_language",      "value": "en",                "description": "System-wide default language"},
        {"key": "core.date_format",      "value": "YYYY-MM-DD",        "description": "Global date format"},
        {"key": "core.number_format",    "value": "#,###.##",          "description": "Global number format"},
        {"key": "core.decimal_precision","value": "2",                 "description": "Global decimal precision"},
        {"key": "core.currency_symbol",  "value": "$",                 "description": "Global currency symbol"},
        {"key": "core.language_default", "value": "en",                "description": "Global default language"},
    ]
    existing = {
        row[0]
        for row in db.query(ArasSetting.key)
                     .filter(ArasSetting.key.in_([d["key"] for d in defaults]))
                     .all()
    }
    new_rows = [ArasSetting(**d) for d in defaults if d["key"] not in existing]
    if new_rows:
        db.add_all(new_rows)
        db.commit()
    logger.info("Default settings seeded.")


def _seed_erp_rbac(db: Session) -> None:
    try:
        from apps.erp.config.seed_rbac import run_seed
        run_seed(db)
    except ImportError:
        pass
