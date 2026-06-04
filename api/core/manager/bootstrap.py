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
    _seed_i18n(db)
    _seed_framework_rbac(db)
    _run_app_seeds(db)


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

    logger.info("Seeding default widgets...")
    WidgetModel.seed_defaults(db)
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


# claude-sonnet-4-6
def _run_app_seeds(db: Session) -> None:
    """Run every installed app's seed() and the decorator-based seed registry.

    Inverted: core no longer names apps (saas/settings/report). Each app owns its
    seed logic in App.seed(db); core just iterates the app registry. Apps that
    register seeds via @core.seeds.register still fire through registry.run_all.
    """
    from core.base.app import App
    from core.seeds import registry
    from core.seeds.base import run_app_seeds

    registry.run_all(db)

    for app_cls in App._registry.values():
        # Declarative seeds (App.seeds list) — the generic, preferred mechanism.
        run_app_seeds(app_cls, db)

        # # claude-opus-4-8 - Generic per-app RBAC pass
        try:
            _run_app_rbac(app_cls, db)
        except Exception as e:
            db.rollback()
            logger.error("RBAC seed failed for app %s: %s", getattr(app_cls, "app_name", "?"), e, exc_info=True)

        # Legacy imperative App.seed(db) override — kept for apps not yet migrated.
        seed = getattr(app_cls, "seed", None)
        if seed is None:
            continue
        try:
            seed(db)
        except Exception as e:  # one app's seed failing must not abort boot
            db.rollback()
            logger.error("Seed failed for app %s: %s", getattr(app_cls, "app_name", "?"), e, exc_info=True)


def _run_app_rbac(app_cls, db: Session) -> None:
    """# claude-opus-4-8
    Runs RBAC discovery for an app: static file + custom hook.
    """
    import inspect
    from pathlib import Path
    from core.seeds.loader import load_rbac, upsert_permissions

    # 1. Static RBAC file
    rbac_rel_path = getattr(app_cls, "rbac_file", None)
    if rbac_rel_path:
        app_file = inspect.getfile(app_cls)
        rbac_path = Path(app_file).parent / rbac_rel_path
        if rbac_path.exists():
            load_rbac(rbac_path, db)

    # 2. Custom permissions hook
    custom_perms = app_cls.get_custom_permissions(db)
    if custom_perms:
        for perm in custom_perms:
            upsert_permissions(
                db, 
                role_name=perm["role"], 
                resource=perm["resource"], 
                actions=perm["actions"]
            )
        db.commit()
