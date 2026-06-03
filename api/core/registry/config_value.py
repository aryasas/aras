# gemini-flash
from datetime import datetime, timezone
from sqlalchemy import String, JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from ..base.model import Model

class ConfigValue(Model):
    """Stores tenant-specific configuration values."""
    __tablename__ = "core_config_values"
    __unique_together__ = [("scope_key", "field_key")]

    # scope_key: "core" | "module:<app>" | "shared" | "feature:<app>"
    # For now we use the app name or "core"
    scope_key: Mapped[str] = mapped_column(String(100))
    field_key: Mapped[str] = mapped_column(String(100))
    value_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Audit fields are already in Model (updated_at, updated_by)

class ConfigValueAudit(Model):
    """Audit log for configuration changes."""
    __tablename__ = "core_config_value_audit"

    id: Mapped[int] = mapped_column(primary_key=True)
    scope_key: Mapped[str] = mapped_column(String(100), index=True)
    field_key: Mapped[str] = mapped_column(String(100), index=True)
    old_value: Mapped[dict] = mapped_column(JSON, nullable=True)
    new_value: Mapped[dict] = mapped_column(JSON, nullable=True)
    user_id: Mapped[int] = mapped_column(nullable=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
