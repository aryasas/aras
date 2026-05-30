# gemini-flash
from datetime import datetime
from sqlalchemy import String, JSON, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from ..base.model import Model

class AuditLog(Model):
    """Generic audit log for all system changes."""
    __tablename__ = "core_audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(100), index=True)
    user_id: Mapped[int] = mapped_column(nullable=True, index=True)
    table_name: Mapped[str] = mapped_column(String(100), index=True)
    row_id: Mapped[str] = mapped_column(String(100), index=True)
    action: Mapped[str] = mapped_column(String(20), index=True) # "insert", "update", "delete"
    diff_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
