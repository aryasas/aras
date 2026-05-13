from typing import List, Dict, Any, Type, Optional
from sqlalchemy.orm import Session
from ..base.aras import Aras
from ..base.service import Service
from ..base.model import Model

class WorkflowManager(Service):
    """
    Centralized engine for managing document state transitions.
    """

    @classmethod
    def get_available_actions(cls, item: Model, user: Any) -> List[Dict[str, Any]]:
        """
        Returns a list of actions the user can perform on the current item state.
        """
        if not hasattr(item, "__transitions__") or not hasattr(item, "status"):
            return []

        current_state = getattr(item, "status", "Draft")
        available = []
        
        # Delayed import to avoid circular dependencies
        from ..logic.permissions import RBAC

        for trans in item.__transitions__:
            if trans["from"] == current_state:
                # Check permission if defined
                permission = trans.get("permission")
                if permission and not user.is_admin:
                    # Logic to check if user has the specific permission
                    # For now, we use a simple RBAC check
                    if not RBAC.has_permission(None, user, item.__tablename__, permission):
                        continue
                
                available.append({
                    "name": trans.get("name", trans["to"]),
                    "to": trans["to"],
                    "label": trans.get("label", trans["to"]),
                    "icon": trans.get("icon", "ArrowRight")
                })
        
        return available

    @classmethod
    def trigger_action(cls, db: Session, item: Model, action_name: str, user: Any) -> bool:
        """
        Validates and executes a state transition.
        """
        current_state = getattr(item, "status", "Draft")
        
        # Find the transition definition
        transition = None
        for trans in item.__transitions__:
            name = trans.get("name", trans["to"])
            if trans["from"] == current_state and name == action_name:
                transition = trans
                break
        
        if not transition:
            raise ValueError(f"Action '{action_name}' is not valid for current state '{current_state}'")

        # 1. Check Permission
        from ..logic.permissions import RBAC
        permission = transition.get("permission")
        if permission and not user.is_admin:
            if not RBAC.has_permission(db, user, item.__tablename__, permission):
                raise PermissionError(f"User does not have permission '{permission}'")

        # 2. Update Status
        old_state = item.status
        item.status = transition["to"]
        
        # 3. Log the transition (using ActivityLog via AuditManager or manually)
        from .audit_manager import AuditManager
        # ActivityLog will be captured by AuditManager if enabled on the model
        
        return True
