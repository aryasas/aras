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

PII_FIELDS = frozenset({
    'password', 'password_hash', 'token', 'refresh_token', 'secret',
    'email', 'phone', 'address', 'card', 'pan', 'cvv',
    'bank_account', 'tax_id', 'national_id', 'passport',
})

# gpt-5
def _is_pii(col) -> bool:
    return bool(col.info.get("pii")) or col.name.lower() in PII_FIELDS

# claude-sonnet-4-6
class AuditManager(Manager):
    """
    Handles automated auditing for all models marked with the 'audit' feature.
    Uses SQLAlchemy session events to capture changes before they are committed.
    """

    @classmethod
    def register_listeners(cls):
        """Attaches event listeners to the Session class."""
        event.listen(Session, "after_flush", cls.after_flush)

    @classmethod
    def after_flush(cls, session, flush_context):
        """Captures changes and creates ActivityLog records."""
        # Note: We use after_flush because IDs are assigned but transaction not committed yet.
        for obj in session.new:
            if cls._is_auditable(obj):
                cls._log_change(session, obj, "INSERT")

        for obj in session.dirty:
            if cls._is_auditable(obj):
                if session.is_modified(obj):
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
            # Capture field-level diffs
            for col in obj.__table__.columns:
                if col.name in ["updated_at", "updated_by"]:
                    continue
                    
                attr = getattr(obj.__class__, col.name)
                # Ensure it's a regular attribute (not a relationship)
                if hasattr(attr, "property") and hasattr(attr.property, "columns"):
                    history = attr.get_history(obj)
                    if history.has_changes():
                        old_val = history.deleted[0] if history.deleted else None
                        new_val = history.added[0] if history.added else None
                        
                        # Only log if they are actually different (avoid redundant logs)
                        if old_val != new_val:
                            if _is_pii(col):
                                changes[col.name] = ["[redacted]", "[redacted]"]
                            else:
                                changes[col.name] = [cls._serialize(old_val), cls._serialize(new_val)]

        elif action == "INSERT":
            # Log all non-null initial values
            for col in obj.__table__.columns:
                val = getattr(obj, col.name, None)
                if val is not None:
                    if _is_pii(col):
                        changes[col.name] = [None, "[redacted]"]
                    else:
                        changes[col.name] = [None, cls._serialize(val)]

        elif action == "DELETE":
            # Log final state before deletion
            for col in obj.__table__.columns:
                val = getattr(obj, col.name, None)
                if _is_pii(col):
                    changes[col.name] = ["[redacted]", None]
                else:
                    changes[col.name] = [cls._serialize(val), None]

        if action == "UPDATE" and not changes:
            return # No relevant changes

        # gemini-pro: Guard against null resource_id (NotNullViolation)
        res_id = getattr(obj, "id", None)
        if res_id is None:
            return

        log = ActivityLog(
            resource=obj.__tablename__,
            resource_id=res_id,
            action=action,
            changes=changes,
            user_id=getattr(obj, "updated_by", None) or getattr(obj, "created_by", None)
        )
        session.add(log)

    @staticmethod
    def _serialize(val):
        """Converts values to JSON-serializable format."""
        from datetime import datetime, date
        from decimal import Decimal
        if isinstance(val, (datetime, date)):
            return val.isoformat()
        if isinstance(val, Decimal):
            return float(val)
        return val
