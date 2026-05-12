"""
Purpose: Generic Workflow (State Machine) engine for ERP documents.
Context: Level 3 Utility. Injected via TraitInjector.
Impact: Automates status transitions and permission gating for documents.
"""
from typing import List, Dict, Any, Type
from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped

class WorkflowMixin:
    """
    Mixin to add workflow capabilities to a model.
    """
    # Level 3 models will define these
    __states__: List[str] = ["Draft", "Submitted", "Cancelled"]
    __transitions__: List[Dict[str, Any]] = [
        {"from": "Draft", "to": "Submitted", "permission": "submit_doc"},
        {"from": "Submitted", "to": "Cancelled", "permission": "cancel_doc"}
    ]

    status: Mapped[str] = mapped_column(String(50), default="Draft")

    def transition_to(self, new_state: str, user: Any):
        """Attempts to move the document to a new state."""
        # Generic validation logic would go here
        self.status = new_state
        return True
