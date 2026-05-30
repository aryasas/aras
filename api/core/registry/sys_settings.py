from sqlalchemy import String, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..base.model import Model
from ..base.field import Field
from typing import Optional

class Settings(Model):
    __tablename__ = "core_settings"
    __public_read__ = True
    __unique_together__ = [("namespace", "key")]

    namespace: Mapped[str] = Field(String(60), index=True, label="Namespace", searchable=True)
    key: Mapped[str] = Field(String(100), label="Setting Key", searchable=True)
    value: Mapped[str] = Field(Text, label="Value", ui_type="textarea")
    value_type: Mapped[str] = Field(String(20), default="str", label="Value Type")
    is_secret: Mapped[bool] = Field(Boolean, default=False, label="Is Secret")
    description: Mapped[str] = Field(String(255), nullable=True, label="Description")
    
    updated_by: Mapped[Optional[int]] = mapped_column(ForeignKey("core_users.id"), nullable=True)
