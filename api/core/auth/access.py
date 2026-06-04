# claude-opus-4-8
"""User ↔ org access (framework-tier).

Links a user to an org via a default access role. org_id=NULL means all orgs.
Domain-agnostic: depends only on core (User, Role, Permission). Products that
need org-scoped data filtering build on top of get_access().
"""
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, Session
from typing import Optional

from core.registry.role import Role
from core.registry.permission import Permission
from core.base.model import Model

DEFAULT_ROLE_NAME = "User"
ACCESS_RESOURCE = "access"


class UserAccess(Model):
    """Links a user to an org with an access role. org_id=NULL means all orgs."""
    __tablename__ = "core_user_access"
    __features__ = []

    user_id: Mapped[int] = mapped_column(ForeignKey("core_users.id"), index=True)
    org_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("core_roles.id"))


# claude-opus-4-8
def ensure_default_role(db: Session) -> Role:
    role = db.query(Role).filter(Role.name == DEFAULT_ROLE_NAME).first()
    if not role:
        role = Role(name=DEFAULT_ROLE_NAME, description="Default application access")
        db.add(role)
        db.flush()
        for action in ("READ", "WRITE"):
            db.add(Permission(role_id=role.id, resource=ACCESS_RESOURCE, action=action))
        db.commit()
        db.refresh(role)
    return role


# claude-opus-4-8
def get_access(db: Session, user_id: int) -> dict:
    role = db.query(Role).filter(Role.name == DEFAULT_ROLE_NAME).first()
    if not role:
        return {"scope": "NONE", "org_ids": []}
    rows = db.query(UserAccess).filter(
        UserAccess.user_id == user_id,
        UserAccess.role_id == role.id,
    ).all()
    if not rows:
        return {"scope": "NONE", "org_ids": []}
    if any(r.org_id is None for r in rows):
        return {"scope": "ALL", "org_ids": []}
    return {"scope": "SPECIFIC", "org_ids": [r.org_id for r in rows]}


# claude-opus-4-8
def clear_access(db: Session, user_id: int, role_id: int):
    db.query(UserAccess).filter(
        UserAccess.user_id == user_id,
        UserAccess.role_id == role_id,
    ).delete()
    db.flush()
