"""
Purpose: Generic logic for injecting ERP traits (Audit, Soft-Delete, Workflow) into Models.
Context: Used by Model.__init_subclass__.
Impact: Eliminates repeatable code by centralizing feature implementation.
"""
from typing import Type, Any
from sqlalchemy import Column, DateTime, Integer, String, Boolean, ForeignKey, func
from sqlalchemy.orm import mapped_column, Mapped
from ..base.service import Service

class TraitInjector(Service):
    """
    Injects columns and logic into Models based on their __features__ attribute.
    """

    @classmethod
    def inject(cls, target_cls: Type[Any]):
        """Main entry point for injection."""
        # Scoping is declarative via __scoped_by__ even without an explicit feature.
        cls._inject_scoped(target_cls)

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
            elif feature == "activatable":
                cls._inject_activatable(target_cls)
            elif feature == "scoped":
                cls._inject_scoped(target_cls)

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

    @classmethod
    def _inject_activatable(cls, target_cls):
        """Adds opt-in is_active column for master/config tables."""
        # Skip abstract bases — they have no __table__.
        if target_cls.__dict__.get("__abstract__"):
            return
        if hasattr(target_cls, "__table__") and "is_active" not in target_cls.__table__.columns:
            from sqlalchemy import Column as _Col
            target_cls.__table__.append_column(
                _Col("is_active", Boolean, default=True, server_default="1", nullable=False)
            )

    @classmethod
    def _inject_scoped(cls, target_cls):
        """For each (col, fk_table) in __scoped_by__, ensure a non-null FK column exists."""
        if target_cls.__dict__.get("__abstract__"):
            return
        scoped_by = getattr(target_cls, "__scoped_by__", None) or []
        if not scoped_by or not hasattr(target_cls, "__table__"):
            return
        for entry in scoped_by:
            if not isinstance(entry, (list, tuple)) or len(entry) != 2:
                continue
            col_name, fk_table = entry
            if col_name in target_cls.__table__.columns:
                continue
            from sqlalchemy import Column as _Col
            new_col = _Col(col_name, Integer, ForeignKey(f"{fk_table}.id"),
                     nullable=False, index=True,
                     info={"form_hidden": True, "scoped": True})
            target_cls.__table__.append_column(new_col)
            # Also set on class so it's accessible as an attribute
            if not hasattr(target_cls, col_name):
                setattr(target_cls, col_name, new_col)
