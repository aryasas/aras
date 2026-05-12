"""
Purpose: DB model for storing a full audit trail of system changes.
Context: Part of Aras.Registry namespace. Populated by AuditManager events.
Impact: Essential for compliance and change history tracking.
"""
from sqlalchemy import String, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from ..base.model import Model

class ActivityLog(Model):
    """
    Stores logs of "Who changed what and when".
    Captures old and new values for every tracked change.
    """
    __tablename__ = "aras_activity_logs"
    __title__ = "Activity Audit Trail"

    resource: Mapped[str] = mapped_column(String(100), index=True) # Table name
    resource_id: Mapped[int] = mapped_column(Integer, index=True)
    action: Mapped[str] = mapped_column(String(20)) # "INSERT", "UPDATE", "DELETE"
    changes: Mapped[dict] = mapped_column(JSON, nullable=True) # {"field": [old, new]}
    note: Mapped[str] = mapped_column(Text, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
