# gemini-flash
import logging
from sqlalchemy.orm import Session
from core.lib.exceptions import RequiredAppError
from core.lib.config import config

logger = logging.getLogger(__name__)

def on_install(db: Session, tenant_id: str):
    """Seed Company defaults."""
    logger.info(f"Installing core_config for tenant: {tenant_id}")
    config.set(db, "core_config.company.name", "My Workspace")
    config.set(db, "core_config.company.base_currency", "USD")
    config.set(db, "core_config.company.timezone", "UTC")
    config.set(db, "core_config.company.locale", "en")
    logger.info("core_config seeded defaults.")

def on_uninstall(db: Session, tenant_id: str):
    """Block uninstall of core_config."""
    raise RequiredAppError("core_config is a mandatory app and cannot be uninstalled.")
