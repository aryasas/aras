from fastapi import HTTPException, status, Depends, Request
from typing import Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, distinct

from ..lib.database import get_db
from ..auth.models import User
from ..auth.service import get_current_user, get_optional_user
from ..base.auth import Auth


def check_permissions(resource: Optional[str] = None, action: str = "READ", allow_public: bool = False):
    """
    Standard dependency for resource-level authorization.
    If resource is None, acts as a simple authentication check.
    If allow_public is True, allows READ access without a user (for public resources).
    """
    async def permission_dependency(
        request: Request,
        user: Any = Depends(get_optional_user if allow_public else get_current_user),
        db: Session = Depends(get_db),
    ):
        company_id = int(request.headers.get("X-Company-ID", 0) or 0)
        request.state.company_id = company_id
        
        if not user:
            if allow_public and action == "READ":
                return None
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        if user.is_admin:
            return user

        if not resource:
            return user

        if not RBAC.has_permission(db, user, resource, action, company_id=company_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions to {action} {resource}"
            )
        return user
    return permission_dependency


class RBAC(Auth):
    @staticmethod
    def has_permission(db: Session, user: User, resource: str, action: str, company_id: Optional[int] = None) -> bool:
        if user.is_admin:
            return True

        from ..registry.role import Role
        from ..registry.user_role import UserRole
        from ..registry.permission import Permission
        
        query = db.query(Permission.id)\
            .join(Role, Role.id == Permission.role_id)\
            .join(UserRole, UserRole.role_id == Role.id)\
            .filter(
                UserRole.user_id == user.id,
                Permission.resource == resource,
                Permission.action == action
            )
        
        if company_id:
            query = query.filter(or_(UserRole.company_id == company_id, UserRole.company_id == None))
        else:
            # If no company_id is provided, only consider global roles (company_id is None)
            query = query.filter(UserRole.company_id == None)
        
        if hasattr(Role, "is_active"):
            query = query.filter(Role.is_active == True)
        if hasattr(Permission, "is_active"):
            query = query.filter(Permission.is_active == True)

        return query.first() is not None

    @staticmethod
    def get_readable_resources(db: Session, user: User) -> set:
        """Returns all resource names the user has READ permission on. Admin bypass is caller's responsibility."""
        from ..registry.role import Role
        from ..registry.user_role import UserRole
        from ..registry.permission import Permission

        query = db.query(Permission.resource)\
            .join(Role, Role.id == Permission.role_id)\
            .join(UserRole, UserRole.role_id == Role.id)\
            .filter(
                UserRole.user_id == user.id,
                Permission.action == "READ"
            )

        if hasattr(Role, "is_active"):
            query = query.filter(Role.is_active == True)
        if hasattr(Permission, "is_active"):
            query = query.filter(Permission.is_active == True)

        rows = query.all()

        return {row[0] for row in rows}

    @staticmethod
    def get_user_companies(db: Session, user: User) -> list[dict]:
        try:
            from apps.erp.config.models import Company
            from ..registry.user_role import UserRole
        except Exception:
            return []

        if user.is_admin:
            rows = db.query(Company.id, Company.name).all()
        else:
            rows = (
                db.query(Company.id, Company.name)
                .join(UserRole, UserRole.company_id == Company.id)
                .filter(UserRole.user_id == user.id, UserRole.company_id.isnot(None))
                .distinct()
                .all()
            )
        return [{"id": r.id, "name": r.name} for r in rows]
