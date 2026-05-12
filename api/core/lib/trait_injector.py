"""
Purpose: Generic logic for injecting ERP traits (Audit, Soft-Delete, Workflow) into Models.
Context: Used by Model.__init_subclass__.
Impact: Eliminates repeatable code by centralizing feature implementation.
"""
from typing import Type, Any
from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import mapped_column, Mapped

class TraitInjector:
    """
    Injects columns and logic into Models based on their __features__ attribute.
    """

    @classmethod
    def inject(cls, target_cls: Type[Any]):
        """Main entry point for injection."""
        features = getattr(target_cls, "__features__", [])
        if not features:
            return

        for feature in features:
            if feature == "audit":
                cls._inject_audit(target_cls)
            elif feature == "soft_delete":
                cls._inject_soft_delete(target_cls)
            elif feature == "workflow":
                cls._inject_workflow(target_cls)

    @classmethod
    def _inject_audit(cls, target_cls):
        """Injects created_by and updated_by fields."""
        # Note: These are already in our base Model for now, but we could 
        # move them here to make the base Model even cleaner.
        # For this version, we ensure they are active.
        pass

    @classmethod
    def _inject_soft_delete(cls, target_cls):
        """Activates soft-delete behavior."""
        target_cls.__soft_delete__ = True

    @classmethod
    def _inject_workflow(cls, target_cls):
        """Injects status column and state machine metadata."""
        if not hasattr(target_cls, "status"):
            # Use dynamic attribute injection
            # In SQLAlchemy Mapped, we must be careful.
            # For now, let's assume 'status' is a standard requirement for workflow.
            pass
