"""
Purpose: DB model for registering relationships between data resources.
Context: Part of Aras.Registry namespace.
Impact: Enables the UI to automatically handle lookups, child tables, and associations.
"""
from sqlalchemy import String, ForeignKey, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from ..base.model import Model
from ..base.field import Field

class LinkModel(Model):
    """Stores metadata about relationships between models."""
    __tablename__ = "aras_links"

    source_resource_id: Mapped[int] = Field(ForeignKey("aras_resources.id"), index=True, display_column="title")
    target_resource_id: Mapped[int] = Field(ForeignKey("aras_resources.id"), index=True, display_column="title")
    
    # The name of the field in the source model that holds the relationship (e.g., 'customer_id')
    # For virtual/reverse links (like 'lines' in Invoice), this might be the relationship name.
    field_name: Mapped[str] = mapped_column(String(100))
    
    # Type of link: 'lookup' (Many-to-One), 'child' (One-to-Many), 'bridge' (Many-to-Many)
    link_type: Mapped[str] = mapped_column(String(50), default="lookup")
    
    label: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # If True, this link should be displayed as a child tab/grid in the UI
    show_as_child: Mapped[bool] = mapped_column(default=False)

    # Human-readable column to display for this link (overrides target's default)
    display_column: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Configuration for specific behaviors (e.g., which field to display from target)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
