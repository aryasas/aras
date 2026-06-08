"""Access RBAC seed — idempotent.

Creates the default User role + permissions and assigns the admin user to all
orgs. Safe to re-run: skips anything that already exists.

Declared on Config.seeds as: RbacSeed("seeds/rbac.yaml") + seed_access.
The YAML role/permission load is handled generically by RbacSeed; this callable
covers the non-declarative part (role-object ensure + admin org assignment).
"""
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# claude-opus-4-8
def seed_access(db: Session) -> None:
    from core.auth.access import ensure_default_role
    from core.auth.models import User

    role = ensure_default_role(db)
    logger.info("Access role ready: id=%s name=%s", role.id, role.name)

    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        _ensure_all_orgs_access(db, admin.id, role.id)

    db.flush()
    logger.info("Access RBAC seed complete.")


seed_access.key = "access_wiring"
seed_access.label = "Access Wiring"
seed_access.optional = False


def _ensure_all_orgs_access(db: Session, user_id: int, role_id: int) -> None:
    from core.auth.access import UserAccess

    exists = db.query(UserAccess).filter(
        UserAccess.user_id == user_id,
        UserAccess.role_id == role_id,
        UserAccess.org_id == None,  # noqa: E711
    ).first()
    if not exists:
        db.add(UserAccess(user_id=user_id, role_id=role_id, org_id=None))
        logger.info("Granted admin all-org access.")
