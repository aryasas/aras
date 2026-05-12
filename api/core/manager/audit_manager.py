"""
Purpose: Logic for capturing and persisting audit trails using SQLAlchemy events.
Context: Level 3 Implementation. Inherits from Manager (Level 2).
Impact: Automates the population of ActivityLog without polluting model code.
"""
from sqlalchemy import event
from sqlalchemy.orm import Session
from ..base.model import Model
from ..registry.activity_log import ActivityLog
from .manager import Manager

class AuditManager(Manager):
    """
    Handles automated auditing for all models marked with the 'audit' feature.
    """

    @classmethod
    def register_listeners(cls):
        """Attaches event listeners to the base Model class."""
        # Use a central event listener for all Aras models
        event.listen(Session, "after_flush", cls.after_flush)

    @classmethod
    def after_flush(cls, session, flush_context):
        """Captures changes and creates ActivityLog records."""
        for obj in session.new:
            if cls._is_auditable(obj):
                cls._log_change(session, obj, "INSERT")

        for obj in session.dirty:
            if cls._is_auditable(obj):
                cls._log_change(session, obj, "UPDATE")

        for obj in session.deleted:
            if cls._is_auditable(obj):
                cls._log_change(session, obj, "DELETE")

    @classmethod
    def _is_auditable(cls, obj):
        """Checks if the model has auditing enabled."""
        return isinstance(obj, Model) and "audit" in getattr(obj, "__features__", [])

    @classmethod
    def _log_change(cls, session, obj, action):
        """Generates the changes dict and persists the log."""
        changes = {}
        if action == "UPDATE":
            for col in obj.__table__.columns:
                history = getattr(obj.__class__, col.name).get_history(obj)
                if history.has_changes():
                    changes[col.name] = [history.deleted[0] if history.deleted else None, 
                                        history.added[0] if history.added else None]
        
        log = ActivityLog(
            resource=obj.__tablename__,
            resource_id=obj.id,
            action=action,
            changes=changes,
            user_id=getattr(obj, "updated_by", None)
        )
        session.add(log)
