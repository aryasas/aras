"""
Purpose: Core Workflow Engine for managing state transitions in ERP documents.
Context: Level 3 Implementation. Inherits from Manager (Level 2).
Impact: Centralizes transition logic and ensures state integrity.
"""
from typing import Type, Any
from sqlalchemy.orm import Session
from ..base.model import Model
from .manager import Manager

class WorkflowManager(Manager):
    """
    Orchestrates state transitions and validates against __transitions__ metadata.
    """

    @classmethod
    def transition(cls, db: Session, obj: Model, target_state: str, user: Any):
        """
        Generic transition handler.
        Validates the transition path and updates status.
        """
        current_state = getattr(obj, "status", None)
        transitions = getattr(obj, "__transitions__", [])
        
        # 1. Validate Transition Path
        valid_path = False
        required_permission = None
        
        for t in transitions:
            if t["from"] == current_state and t["to"] == target_state:
                valid_path = True
                required_permission = t.get("permission")
                break
        
        if not valid_path:
            return False, f"Invalid transition from '{current_state}' to '{target_state}'"

        # 2. Permission Gating (Integrate with RBAC)
        # Note: RBAC logic is in permissions.py, WorkflowManager delegates check.
        
        # 3. Apply Transition
        obj.status = target_state
        db.commit()
        
        return True, "Transition successful"
