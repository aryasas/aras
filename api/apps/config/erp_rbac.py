from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, Session
from typing import Optional

from core.auth.models import User
from core.registry.role import Role
from core.registry.permission import Permission
from core.base.model import Model

ERP_ROLE_NAME = "ERP User"
ERP_RESOURCE = "erp"


class ErpUserAccess(Model):
    """Links a user to an org with an ERP role. org_id=NULL means all orgs."""
    __tablename__ = "config_user_access"
    __features__ = []

    user_id: Mapped[int] = mapped_column(ForeignKey("core_users.id"), index=True)
    org_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("core_roles.id"))


def ensure_erp_role(db: Session) -> Role:
    role = db.query(Role).filter(Role.name == ERP_ROLE_NAME).first()
    if not role:
        role = Role(name=ERP_ROLE_NAME, description="ERP system access")
        db.add(role)
        db.flush()
        for action in ("READ", "WRITE"):
            db.add(Permission(role_id=role.id, resource=ERP_RESOURCE, action=action))
        db.commit()
        db.refresh(role)
    return role


def get_access(db: Session, user_id: int) -> dict:
    role = db.query(Role).filter(Role.name == ERP_ROLE_NAME).first()
    if not role:
        return {"scope": "NONE", "org_ids": []}
    rows = db.query(ErpUserAccess).filter(
        ErpUserAccess.user_id == user_id,
        ErpUserAccess.role_id == role.id,
    ).all()
    if not rows:
        return {"scope": "NONE", "org_ids": []}
    if any(r.org_id is None for r in rows):
        return {"scope": "ALL", "org_ids": []}
    return {"scope": "SPECIFIC", "org_ids": [r.org_id for r in rows]}


def clear_access(db: Session, user_id: int, role_id: int):
    db.query(ErpUserAccess).filter(
        ErpUserAccess.user_id == user_id,
        ErpUserAccess.role_id == role_id,
    ).delete()
    db.flush()


def get_user_org_list(db: Session, user: User) -> list[dict]:
    """Plugin integration point — called by core/auth/routes.py."""
    from apps.config.models import Organization
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
