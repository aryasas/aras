from fastapi import HTTPException, status, Depends
from typing import List, Callable, Any
from ..auth.models import User
from ..auth import get_current_user

def check_permissions(required_admin: bool = False):
    """
    Dependency to check if the current user has required permissions.
    """
    async def permission_dependency(user: Any = Depends(get_current_user)):
        if required_admin and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return user
    return permission_dependency

class RBAC:
    """
    Placeholder for more advanced Role-Based Access Control logic.
    """
    @staticmethod
    def has_permission(user: User, permission: str) -> bool:
        if user.is_admin:
            return True
        # Future implementation: check roles and permissions table
        return False
