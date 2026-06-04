"""
Purpose: DB model for registering data resources (tables).
Context: Part of Aras.Registry namespace. Link between Apps and Models.
Impact: Stores traits (features) and layout metadata for the GUI.
"""
from sqlalchemy import String, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base.model import Model
from ..base.field import Field
from typing import List

class ResourceModel(Model):
    """Stores metadata about models/tables registered in the system."""
    __tablename__ = "core_resources"

    app_id: Mapped[int] = Field(ForeignKey("core_apps.id"), display_column="name")
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True) # e.g. "sale_invoice"
    title: Mapped[str] = mapped_column(String(100))
    model_class: Mapped[str] = mapped_column(String(100)) # e.g. "SaleInvoice"
    features: Mapped[list] = mapped_column(JSON, default=list) # e.g. ["audit", "workflow"]
    scoped_by: Mapped[list] = mapped_column(JSON, default=list) # e.g. [["company_id","core_organizations"]]
    layout: Mapped[list] = mapped_column(JSON, default=list)
    is_dynamic: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    fields: Mapped[List["FieldModel"]] = relationship("FieldModel", backref="resource", cascade="all, delete-orphan")
    links: Mapped[List["LinkModel"]] = relationship(
        "LinkModel", 
        primaryjoin="ResourceModel.id == LinkModel.source_resource_id",
        cascade="all, delete-orphan"
    )
