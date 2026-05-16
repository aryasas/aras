import os
import logging
from datetime import datetime
from typing import Dict, Any

from .registry import tenant_registry

logger = logging.getLogger(__name__)

ADMIN_DB_URL = os.getenv("ADMIN_DATABASE_URL")


def _run_alembic_migrations(db_url: str):
    """
    Placeholder function to run Alembic migrations on a new tenant database.
    This should be replaced with the actual Alembic command execution logic.
    """
    # In a real implementation, this would invoke Alembic programmatically
    # from alembic.config import Config
    # from alembic import command
    #
    # alembic_cfg = Config("alembic.ini")
    # alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    # command.upgrade(alembic_cfg, "head")
    logger.info(f"Running migrations for database at {db_url[:30]}...")
    # For now, we'll just log it.
    # In a real scenario, this might involve running a subprocess or using Alembic's API
    pass


def provision_tenant(tenant_id: str, db_name: str) -> Dict[str, Any]:
    """
    Provisions a new tenant by creating a dedicated PostgreSQL database.

    Steps:
    1. Connect to the administrative 'postgres' database.
    2. Create a new database for the tenant.
    3. (Placeholder) Run Alembic migrations to set up the schema.
    4. Register the new tenant in the tenant registry.

    Args:
        tenant_id: The unique identifier for the new tenant.
        db_name: The name for the new PostgreSQL database.

    Returns:
        A dictionary containing the connection information for the new tenant.

    Raises:
        Exception: If any step of the provisioning process fails.
    """
    if not ADMIN_DB_URL:
        raise ConnectionError("ADMIN_DATABASE_URL is not configured.")

    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        raise RuntimeError("psycopg2 is required for tenant provisioning. Run: pip install psycopg2-binary")

    conn = None
    try:
        conn = psycopg2.connect(ADMIN_DB_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if database already exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        if cursor.fetchone():
            raise ValueError(f"Database '{db_name}' already exists.")

        logger.info(f"Creating database '{db_name}' for tenant '{tenant_id}'...")
        cursor.execute(f'CREATE DATABASE "{db_name}"')
        logger.info(f"Database '{db_name}' created successfully.")

        cursor.close()

        db_parts = psycopg2.connect(ADMIN_DB_URL).get_dsn_parameters()
        tenant_db_url = f"postgresql://{db_parts['user']}:{db_parts['password']}@{db_parts['host']}:{db_parts['port']}/{db_name}"

        # Run migrations on the new database
        _run_alembic_migrations(tenant_db_url)
        logger.info(f"Migrations completed for tenant '{tenant_id}'.")

        # Register the tenant
        tenant_info = tenant_registry.register(tenant_id, db_url=tenant_db_url, meta={'db_name': db_name})
        logger.info(f"Tenant '{tenant_id}' successfully provisioned and registered.")

        return tenant_info

    except Exception as e:
        logger.error(f"Failed to provision tenant '{tenant_id}': {e}", exc_info=True)
        # Attempt to clean up by dropping the database if it was created
        try:
            if conn and not conn.closed:
                cursor = conn.cursor()
                cursor.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
                cursor.close()
                logger.info(f"Cleaned up partially created database '{db_name}'.")
        except Exception as cleanup_e:
            logger.error(f"Failed to clean up database during error handling: {cleanup_e}")
        raise
    finally:
        if conn and not conn.closed:
            conn.close()


def deprovision_tenant(tenant_id: str) -> bool:
    """
    De-provisions a tenant by 'soft-deleting' their database.

    The database is renamed to include a timestamp and a '_deleted_' prefix,
    allowing for a grace period before permanent deletion.

    Args:
        tenant_id: The ID of the tenant to de-provision.

    Returns:
        True if the de-provisioning was successful, False otherwise.
    """
    if not ADMIN_DB_URL:
        raise ConnectionError("ADMIN_DATABASE_URL is not configured.")

    tenant_info = tenant_registry.get(tenant_id)
    if not tenant_info or 'meta' not in tenant_info or 'db_name' not in tenant_info['meta']:
        logger.warning(f"Tenant '{tenant_id}' not found in registry or is missing db_name metadata.")
        return False

    db_name = tenant_info['meta']['db_name']
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    deleted_db_name = f"_deleted_{timestamp}_{db_name}"

    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        raise RuntimeError("psycopg2 is required for tenant provisioning. Run: pip install psycopg2-binary")

    conn = None
    try:
        conn = psycopg2.connect(ADMIN_DB_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        if not cursor.fetchone():
            logger.warning(f"Database '{db_name}' for tenant '{tenant_id}' not found. Removing from registry anyway.")
            tenant_registry.unregister(tenant_id)
            return True

        logger.info(f"Soft-deleting database for tenant '{tenant_id}' by renaming '{db_name}' to '{deleted_db_name}'...")
        cursor.execute(f'ALTER DATABASE "{db_name}" RENAME TO "{deleted_db_name}"')
        logger.info("Database renamed successfully.")

        cursor.close()

        # Remove the tenant from the active registry
        tenant_registry.unregister(tenant_id)
        logger.info(f"Tenant '{tenant_id}' unregistered successfully.")

        return True
    except Exception as e:
        logger.error(f"Failed to deprovision tenant '{tenant_id}': {e}", exc_info=True)
        return False
    finally:
        if conn and not conn.closed:
            conn.close()
