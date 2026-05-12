"""
Purpose: DB model for storing a full audit trail of system changes.
Context: Part of Aras.Registry namespace. Populated by AuditManager events.
Impact: Essential for compliance and change history tracking.
"""
from sqlalchemy import String, Integer, JSON, Text
from sqlalchemy.orm import Mapped
from ..base.model import Model
from ..base.field import Field

class ActivityLog(Model):
    """
    Stores logs of "Who changed what and when".
    Captures old and new values for every tracked change.
    """
    __tablename__ = "aras_activity_logs"
    __title__ = "Activity Audit Trail"

    resource: Mapped[str] = Field(String(100), index=True, label="Resource")
    resource_id: Mapped[int] = Field(Integer, index=True, label="Record ID")
    action: Mapped[str] = Field(String(20), label="Action")
    changes: Mapped[dict] = Field(JSON, nullable=True, label="Data Changes")
    note: Mapped[str] = Field(Text, nullable=True, label="Internal Note")
    user_id: Mapped[int] = Field(Integer, nullable=True, index=True, label="Changed By User")
