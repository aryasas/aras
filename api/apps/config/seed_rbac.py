"""ERP RBAC seed — idempotent.

Creates the ERP User role + permissions and assigns the admin user to all orgs.
Safe to re-run: skips anything that already exists.
"""
import logging
from sqlalchemy.orm import Session
from core.seeds.registry import register

logger = logging.getLogger(__name__)


# claude-sonnet-4-6
@register
def run_seed(db: Session) -> None:
    from pathlib import Path
    from core.seeds.loader import load_rbac
    from apps.config.erp_rbac import ensure_erp_role, ErpUserAccess
    from core.auth.models import User

    # Load granular ERP roles from YAML
    seed_file = Path(__file__).parent.parent / "seeds" / "rbac_erp.yaml"
    load_rbac(seed_file, db)

    role = ensure_erp_role(db)
    logger.info("ERP role ready: id=%s name=%s", role.id, role.name)

    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        _ensure_all_orgs_access(db, admin.id, role.id)

    db.commit()
    logger.info("ERP RBAC seed complete.")


def _ensure_all_orgs_access(db: Session, user_id: int, role_id: int) -> None:
    from apps.config.erp_rbac import ErpUserAccess

    exists = db.query(ErpUserAccess).filter(
        ErpUserAccess.user_id == user_id,
        ErpUserAccess.role_id == role_id,
        ErpUserAccess.org_id == None,  # noqa: E711
    ).first()
    if not exists:
        db.add(ErpUserAccess(user_id=user_id, role_id=role_id, org_id=None))
        logger.info("Granted admin all-org ERP access.")
