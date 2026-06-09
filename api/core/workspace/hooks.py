# gemini-flash
import logging
from sqlalchemy.orm import Session
from core.lib.exceptions import RequiredAppError

logger = logging.getLogger(__name__)

def on_install(db: Session, tenant_id: str):
    """Install core_config app. Organization identity (name/currency/timezone/locale)
    is owned by the `core_organizations` model and seeded there — not duplicated here."""
    logger.info(f"Installing core_config for tenant: {tenant_id}")

def on_uninstall(db: Session, tenant_id: str):
    """Block uninstall of core_config."""
    raise RequiredAppError("core_config is a mandatory app and cannot be uninstalled.")
