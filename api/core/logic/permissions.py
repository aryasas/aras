from fastapi import HTTPException, status, Depends
from typing import Any, Optional
from sqlalchemy.orm import Session

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
        user: Any = Depends(get_optional_user if allow_public else get_current_user),
        db: Session = Depends(get_db)
    ):
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

        if not RBAC.has_permission(db, user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions to {action} {resource}"
            )
        return user
    return permission_dependency


class RBAC(Auth):
    @staticmethod
    def has_permission(db: Session, user: User, resource: str, action: str) -> bool:
        if user.is_admin:
            return True

        from ..registry.role import Role
        from ..registry.user_role import UserRole
        from ..registry.permission import Permission

        return db.query(Permission.id)\
            .join(Role, Role.id == Permission.role_id)\
            .join(UserRole, UserRole.role_id == Role.id)\
            .filter(
                UserRole.user_id == user.id,
                Permission.resource == resource,
                Permission.action == action,
                Role.is_active == True,
                Permission.is_active == True
            ).first() is not None

    @staticmethod
    def get_readable_resources(db: Session, user: User) -> set:
        """Returns all resource names the user has READ permission on. Admin bypass is caller's responsibility."""
        from ..registry.role import Role
        from ..registry.user_role import UserRole
        from ..registry.permission import Permission

        rows = db.query(Permission.resource)\
            .join(Role, Role.id == Permission.role_id)\
            .join(UserRole, UserRole.role_id == Role.id)\
            .filter(
                UserRole.user_id == user.id,
                Permission.action == "READ",
                Role.is_active == True,
                Permission.is_active == True
            ).all()

        return {row[0] for row in rows}
