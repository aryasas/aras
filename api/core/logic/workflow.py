"""
Purpose: Generic Workflow (State Machine) engine for ERP documents.
Context: Level 3 Utility. Injected via TraitInjector.
Impact: Automates status transitions and permission gating for documents.
"""
from typing import List, Dict, Any, Type
from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped
from ..base.aras import Aras

class WorkflowMixin(Aras):
    """
    Mixin to add workflow capabilities to a model.
    """
    # Level 3 models will define these
    __states__: List[str] = ["Draft", "Submitted", "Cancelled"]
    __transitions__: List[Dict[str, Any]] = [
        {"name": "submit", "from": "Draft", "to": "Submitted", "label": "Submit", "permission": "submit_doc", "icon": "Check"},
        {"name": "cancel", "from": "Submitted", "to": "Cancelled", "label": "Cancel", "permission": "cancel_doc", "icon": "X"}
    ]

    status: Mapped[str] = mapped_column(String(50), default="Draft", info={"label": "Status", "read_only": True})

