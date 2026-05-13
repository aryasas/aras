from fastapi import HTTPException, status, Depends
from typing import List, Callable, Any, Optional
from sqlalchemy.orm import Session

from ..lib.database import get_db
from ..auth.models import User
from ..auth import get_current_user
from ..base.auth import Auth

def check_permissions(resource: Optional[str] = None, action: str = "READ"):
    """
    Standard dependency for resource-level authorization.
    If resource is None, it acts as a simple authentication check (is logged in).
    If resource is provided, it checks if the user has a role with the required action.
    """
    async def permission_dependency(
        user: Any = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        # 1. Admin bypass
        if user.is_admin:
            return user

        # 2. If no resource specified, simple login check is enough
        if not resource:
            return user

        # 3. Check Granular RBAC
        if not RBAC.has_permission(db, user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions to {action} {resource}"
            )
        return user
    return permission_dependency

class RBAC(Auth):
    """
    Engine for Role-Based Access Control logic.
    """
    @staticmethod
    def has_permission(db: Session, user: User, resource: str, action: str) -> bool:
        """
        Checks if a user has the required action permitted on a resource.
        Joins: User -> UserRole -> Role -> Permission
        """
        if user.is_admin:
            return True
        
        # Delayed import to avoid circular dependencies
        from ..registry.role import Role
        from ..registry.user_role import UserRole
        from ..registry.permission import Permission

        # Efficient query to check for permission existence
        permission_exists = db.query(Permission.id)\
            .join(Role, Role.id == Permission.role_id)\
            .join(UserRole, UserRole.role_id == Role.id)\
            .filter(
                UserRole.user_id == user.id,
                Permission.resource == resource,
                Permission.action == action,
                Role.is_active == True,
                Permission.is_active == True
            ).first()

        return permission_exists is not None
