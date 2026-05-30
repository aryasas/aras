import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from sqlalchemy import create_engine, text
from .registry import tenant_registry

logger = logging.getLogger(__name__)


def _get_admin_connection():
    """Return a SQLAlchemy engine connected to the postgres admin DB."""
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    pw = f":{password}" if password else ""
    url = f"postgresql+psycopg2://{user}{pw}@{host}:{port}/postgres"
    return create_engine(url, isolation_level="AUTOCOMMIT")


def _build_tenant_db_url(db_name: str) -> str:
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    pw = f":{password}" if password else ""
    return f"postgresql+psycopg2://{user}{pw}@{host}:{port}/{db_name}"


def provision_tenant(tenant_id: str, db_name: str, apps: tuple = ("core_config",), extra: tuple = ()) -> Dict[str, Any]:
    """
    Provision a new tenant by creating a dedicated database,
    running schema migrations, and registering the tenant.
    Then installs required and requested apps.
    """
    existing = tenant_registry.get(tenant_id)
    if existing:
        raise ValueError(f"Tenant '{tenant_id}' is already registered.")

    admin_engine = _get_admin_connection()
    try:
        with admin_engine.connect() as conn:
            result = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": db_name})
            if result.fetchone():
                raise ValueError(f"Database '{db_name}' already exists.")

            logger.info(f"Creating database '{db_name}' for tenant '{tenant_id}'...")
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
            logger.info(f"Database '{db_name}' created.")
    finally:
        admin_engine.dispose()

    tenant_db_url = _build_tenant_db_url(db_name)

    # Run Alembic schema migrations on the new tenant DB
    try:
        from alembic import command
        from alembic.config import Config
        api_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cfg = Config(os.path.join(api_root, "alembic.ini"))
        cfg.set_main_option("sqlalchemy.url", tenant_db_url)
        command.upgrade(cfg, "head")
        logger.info(f"Schema migrated for tenant '{tenant_id}'.")
    except Exception as e:
        logger.error(f"Schema sync failed for tenant '{tenant_id}': {e}")
        raise

    tenant_info = tenant_registry.register(tenant_id, db_url=tenant_db_url, meta={"db_name": db_name})
    logger.info(f"Tenant '{tenant_id}' provisioned and registered.")

    # Install apps
    all_apps = list(apps) + list(extra)
    for app_name in all_apps:
        install_app_on_tenant(tenant_id, app_name)

    return tenant_info


def install_app_on_tenant(tenant_id: str, app_name: str):
    """
    Installs an app on an existing tenant by running its on_install hook.
    """
    from core.base.app import App
    from .router import get_tenant_db
    
    app_cls = App._registry.get(app_name)
    if not app_cls:
        # Try to find by app_name if class name is different
        for _, cls in App._registry.items():
            if getattr(cls, "app_name", None) == app_name:
                app_cls = cls
                break
                
    if not app_cls:
        logger.warning(f"App '{app_name}' not found for installation.")
        return

    db = get_tenant_db(tenant_id)
    if not db:
        logger.error(f"Cannot connect to tenant '{tenant_id}' for app installation.")
        return

    try:
        # Run on_install hook
        if hasattr(app_cls, "on_install"):
            logger.info(f"Running on_install for '{app_name}' on tenant '{tenant_id}'")
            app_cls.on_install(db, tenant_id)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to install app '{app_name}' on tenant '{tenant_id}': {e}")
        raise
    finally:
        db.close()


def seed_tenant(tenant_id: str) -> Dict[str, Any]:
    """
    Run basic seed data (org, COA, series, reports) for a tenant database.
    Returns a summary of what was seeded.
    """
    from .router import get_tenant_db
    db = get_tenant_db(tenant_id)
    if not db:
        raise ValueError(f"Cannot connect to tenant '{tenant_id}'.")

    seeded = []
    try:
        from seed_basic import seed_basic_data
        seed_basic_data(db=db)
        seeded.append("basic")

        from apps.config.seed_series import run as seed_series
        seed_series(db=db)
        seeded.append("series")

        from apps.report.seed_reports import run_seed as seed_reports
        from core.aras import Aras
        Org = Aras.Model._registry.get("Organization")
        if Org:
            org = db.query(Org).first()
            if org:
                seed_reports(db, org.id)
                seeded.append("reports")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return {"tenant_id": tenant_id, "seeded": seeded}


def deprovision_tenant(tenant_id: str) -> bool:
    """
    Soft-delete a tenant by renaming their database and unregistering them.
    """
    tenant_info = tenant_registry.get(tenant_id)
    if not tenant_info or "meta" not in tenant_info or "db_name" not in tenant_info["meta"]:
        logger.warning(f"Tenant '{tenant_id}' not found in registry.")
        return False

    db_name = tenant_info["meta"]["db_name"]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    deleted_db_name = f"_deleted_{timestamp}_{db_name}"

    admin_engine = _get_admin_connection()
    try:
        with admin_engine.connect() as conn:
            result = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": db_name})
            if not result.fetchone():
                logger.warning(f"Database '{db_name}' not found. Unregistering only.")
                tenant_registry.unregister(tenant_id)
                return True

            logger.info(f"Renaming '{db_name}' → '{deleted_db_name}'...")
            conn.execute(text(f'ALTER DATABASE "{db_name}" RENAME TO "{deleted_db_name}"'))
            logger.info("Database soft-deleted.")
    finally:
        admin_engine.dispose()

    tenant_registry.unregister(tenant_id)
    logger.info(f"Tenant '{tenant_id}' unregistered.")
    return True
