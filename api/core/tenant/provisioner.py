import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from sqlalchemy import create_engine, text
from .registry import tenant_registry

logger = logging.getLogger(__name__)


def _get_admin_connection():
    """Return a SQLAlchemy engine connected to the postgres admin DB."""
    # gemini-pro: prioritize TENANT_DB_* for multi-db docker setup
    user = os.getenv("TENANT_DB_USER") or os.getenv("DB_USER", "postgres")
    password = os.getenv("TENANT_DB_PASSWORD") or os.getenv("DB_PASSWORD", "")
    host = os.getenv("TENANT_DB_HOST") or os.getenv("DB_HOST", "localhost")
    port = os.getenv("TENANT_DB_PORT") or os.getenv("DB_PORT", "5432")
    pw = f":{password}" if password else ""
    url = f"postgresql+psycopg2://{user}{pw}@{host}:{port}/postgres"
    return create_engine(url, isolation_level="AUTOCOMMIT")


def _build_tenant_db_url(db_name: str) -> str:
    # gemini-pro: prioritize TENANT_DB_* for multi-db docker setup
    user = os.getenv("TENANT_DB_USER") or os.getenv("DB_USER", "postgres")
    password = os.getenv("TENANT_DB_PASSWORD") or os.getenv("DB_PASSWORD", "")
    host = os.getenv("TENANT_DB_HOST") or os.getenv("DB_HOST", "localhost")
    port = os.getenv("TENANT_DB_PORT") or os.getenv("DB_PORT", "5432")
    pw = f":{password}" if password else ""
    return f"postgresql+psycopg2://{user}{pw}@{host}:{port}/{db_name}"


def provision_tenant(tenant_id: str, db_name: str, apps: tuple = ("core_config",), extra: tuple = ()) -> Dict[str, Any]:
    """
    Complete flow for new tenant: Create DB, Run Migrations, Register.
    """
    logger.info(f"Provisioning tenant '{tenant_id}'...")

    # 1. Validation
    if tenant_registry.get(tenant_id):
        raise ValueError(f"Tenant '{tenant_id}' already exists in registry.")

    # 2. Check if DB name is already used (safeguard)
    # TODO: add DB check via admin connection

    # 3. Create Database
    admin_engine = _get_admin_connection()
    try:
        with admin_engine.connect() as conn:
            # Check if exists
            res = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")).fetchone()
            if res:
                raise ValueError(f"Database '{db_name}' already exists.")
            
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
            logger.info(f"Database '{db_name}' created.")
    finally:
        admin_engine.dispose()

    tenant_db_url = _build_tenant_db_url(db_name)
    engine = create_engine(tenant_db_url)

    # gemini-pro: initialize schema via metadata first to ensure all tables exist for mixed migrations
    try:
        from core import Aras
        # Ensure all apps are discovered so their models are in metadata
        Aras.logic.discovery.discover_apps(package_path="apps")
        # logger.info(f"Tables in metadata: {list(Aras.Base.metadata.tables.keys())}")
        Aras.Base.metadata.create_all(bind=engine)
        logger.info(f"Schema initialized via metadata for tenant '{tenant_id}'.")
    finally:
        engine.dispose()

    # Run Alembic schema migrations on the new tenant DB to ensure alembic_version is set
    try:
        from alembic import command
        from alembic.config import Config
        api_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cfg = Config(os.path.join(api_root, "alembic.ini"))
        # gemini-pro: make script_location absolute for docker environments
        cfg.set_main_option("script_location", os.path.join(api_root, "alembic"))
        cfg.set_main_option("sqlalchemy.url", tenant_db_url)
        # Use stamp head because we already created all tables via metadata.create_all.
        # This avoids issues where migrations try to modify framework tables (like saas_plan)
        # that might not behave well in a tenant-specific migration context.
        command.stamp(cfg, "head")
        logger.info(f"Schema marked as head for tenant '{tenant_id}'.")
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
    from core import Aras
    from .router import get_tenant_db
    
    app_cls = None
    for cls in Aras.App._registry:
        if getattr(cls, "app_name", None) == app_name:
            app_cls = cls
            break
                
    if not app_cls:
        logger.warning(f"App '{app_name}' not found for installation.")
        return

    db_gen = get_tenant_db(tenant_id)
    try:
        db = next(db_gen)
    except Exception as e:
        logger.error(f"Failed to get DB for tenant '{tenant_id}': {e}")
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
        try:
            next(db_gen)
        except StopIteration:
            pass


def seed_tenant(tenant_id: str) -> Dict[str, Any]:
    """
    Run basic seed data (org, COA, series, reports) for a tenant database.
    Returns a summary of what was seeded.
    """
    from .router import get_tenant_db
    # gemini-pro: get_tenant_db is a generator
    db_gen = get_tenant_db(tenant_id)
    try:
        db = next(db_gen)
    except StopIteration:
        raise ValueError(f"Cannot connect to tenant '{tenant_id}'.")
    except Exception as e:
        raise ValueError(f"Cannot connect to tenant '{tenant_id}': {e}")

    seeded = []
    try:
        from seed_basic import seed_basic_data
        seed_basic_data(db=db)
        seeded.append("basic")

        from apps.config.seed_series import run as seed_series
        seed_series(db=db)
        seeded.append("series")

        from apps.report.seed_reports import run_seed as seed_reports
        from apps.config.models import Organization
        org = db.query(Organization).first()
        if org:
            seed_reports(db, org.id)
            seeded.append("reports")

        db.commit()
        return {"tenant_id": tenant_id, "seeded": seeded}
    except Exception as e:
        db.rollback()
        logger.error(f"Seeding failed for tenant '{tenant_id}': {e}")
        raise
    finally:
        # Close generator/session
        try:
            next(db_gen)
        except (StopIteration, Exception):
            pass


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
    deleted_db_name = f"deleted_{timestamp}_{db_name}"

    admin_engine = _get_admin_connection()
    try:
        with admin_engine.connect() as conn:
            # Terminate active connections
            conn.execute(text(f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{db_name}' AND pid <> pg_backend_pid()
            """))
            # Rename database
            conn.execute(text(f'ALTER DATABASE "{db_name}" RENAME TO "{deleted_db_name}"'))
            logger.info("Database soft-deleted.")
    finally:
        admin_engine.dispose()

    tenant_registry.unregister(tenant_id)
    logger.info(f"Tenant '{tenant_id}' unregistered.")
    return True
