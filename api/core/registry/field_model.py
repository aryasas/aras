"""
Purpose: DB model for registering field-level metadata and GUI overrides.
Context: Part of Aras.Registry namespace. Child of ResourceModel.
Impact: Allows users to override labels, types, and visibility from the GUI.
"""
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..base.model import Model
from ..base.field import Field

class FieldModel(Model):
    """Stores metadata about individual fields/columns."""
    __tablename__ = "aras_fields"
    __title__ = "Field Registry"

    resource_id: Mapped[int] = Field(ForeignKey("aras_resources.id"), display_column="title")
    name: Mapped[str] = mapped_column(String(100), index=True)
    label: Mapped[str] = mapped_column(String(100))
    ui_type: Mapped[str] = mapped_column(String(50), default="string")
    is_required: Mapped[bool] = mapped_column(default=False)
    is_read_only: Mapped[bool] = mapped_column(default=False)
    is_hidden: Mapped[bool] = mapped_column(default=False)
    is_searchable: Mapped[bool] = mapped_column(default=True)
    is_override: Mapped[bool] = mapped_column(default=False) # True if modified via GUI

    # Lookup Metadata
    link_column: Mapped[str] = mapped_column(String(100), nullable=True) # e.g. "id" or "name"
    display_column: Mapped[str] = mapped_column(String(100), nullable=True) # e.g. "name"
