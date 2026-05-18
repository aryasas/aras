from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.lib.database import get_db
from core.logic.permissions import check_permissions
from core.auth.models import User
from core.registry.role import Role
from .erp_rbac import ErpUserAccess, ensure_erp_role, get_access, clear_access

erp_rbac_router = APIRouter()


class SetAccessRequest(BaseModel):
    scope: str  # "ALL" | "SPECIFIC" | "NONE"
    org_ids: list[int] = []


@erp_rbac_router.get("/erp-rbac/orgs")
def list_orgs(
    db: Session = Depends(get_db),
    _: User = Depends(check_permissions(resource=None)),
):
    from apps.erp.config.models import Organization
    orgs = db.query(Organization).order_by(Organization.name).all()
    return [{"id": o.id, "name": o.name} for o in orgs]


@erp_rbac_router.get("/erp-rbac/users")
def list_users_access(
    db: Session = Depends(get_db),
    _: User = Depends(check_permissions(resource=None)),
):
    from apps.erp.config.models import Organization
    users = db.query(User).order_by(User.username).all()
    result = []
    for u in users:
        if u.is_admin:
            result.append({
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "is_admin": True,
                "scope": "ALL",
                "org_ids": [],
                "org_names": [],
            })
            continue
        access = get_access(db, u.id)
        org_names: list[str] = []
        if access["scope"] == "SPECIFIC" and access["org_ids"]:
            orgs = db.query(Organization).filter(Organization.id.in_(access["org_ids"])).all()
            org_names = [o.name for o in orgs]
        result.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_admin": False,
            "scope": access["scope"],
            "org_ids": access["org_ids"],
            "org_names": org_names,
        })
    return result


@erp_rbac_router.get("/erp-rbac/users/{user_id}")
def get_user_access(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(check_permissions(resource=None)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    access = get_access(db, user_id)
    return {"id": user.id, "username": user.username, "email": user.email, **access}


@erp_rbac_router.post("/erp-rbac/users/{user_id}")
def set_user_access(
    user_id: int,
    body: SetAccessRequest,
    db: Session = Depends(get_db),
    _: User = Depends(check_permissions(resource=None)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    role = ensure_erp_role(db)
    clear_access(db, user_id, role.id)
    if body.scope == "ALL":
        db.add(ErpUserAccess(user_id=user_id, role_id=role.id, org_id=None))
    elif body.scope == "SPECIFIC":
        if not body.org_ids:
            raise HTTPException(status_code=400, detail="org_ids required for SPECIFIC scope")
        for oid in body.org_ids:
            db.add(ErpUserAccess(user_id=user_id, role_id=role.id, org_id=oid))
    db.commit()
    return get_access(db, user_id)


@erp_rbac_router.delete("/erp-rbac/users/{user_id}")
def revoke_user_access(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(check_permissions(resource=None)),
):
    role = db.query(Role).filter(Role.name == "ERP User").first()
    if role:
        clear_access(db, user_id, role.id)
        db.commit()
    return {"ok": True}
