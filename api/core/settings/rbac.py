# claude-opus-4-8
"""Product-tier org-access wiring.

The access model + role/scope logic live framework-side in ``core.auth.access``.
This module keeps only the part that depends on the product's Organization model.
"""
from sqlalchemy.orm import Session

from core.auth.models import User
from core.auth.access import UserAccess, ensure_default_role, get_access, clear_access

__all__ = [
    "UserAccess", "ensure_default_role", "get_access",
    "clear_access", "get_user_org_list",
]


def get_user_org_list(db: Session, user: User) -> list[dict]:
    """Plugin integration point — called by core/auth/routes.py."""
    from core.workspace.models import Organization
    def _row(r): return {"id": r.id, "name": r.name, "is_default": r.is_default, "is_group": r.is_group}
    if user.is_admin:
        rows = db.query(Organization).order_by(Organization.name).all()
        return [_row(r) for r in rows]
    access = get_access(db, user.id)
    if access["scope"] == "NONE":
        return []
    if access["scope"] == "ALL":
        rows = db.query(Organization).order_by(Organization.name).all()
        return [_row(r) for r in rows]
    rows = db.query(Organization).filter(Organization.id.in_(access["org_ids"])).all()
    return [_row(r) for r in rows]
