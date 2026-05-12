"""
Purpose: DB model for registering data resources (tables).
Context: Part of Aras.Registry namespace. Link between Apps and Models.
Impact: Stores traits (features) and layout metadata for the GUI.
"""
from sqlalchemy import String, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..base.model import Model
from ..base.field import Field

class ResourceModel(Model):
    """Stores metadata about models/tables registered in the system."""
    __tablename__ = "aras_resources"
    __title__ = "Resource Registry"

    app_id: Mapped[int] = Field(ForeignKey("aras_apps.id"), display_column="name")
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True) # e.g. "sale_invoice"
    title: Mapped[str] = mapped_column(String(100))
    model_class: Mapped[str] = mapped_column(String(100)) # e.g. "SaleInvoice"
    features: Mapped[list] = mapped_column(JSON, default=list) # e.g. ["audit", "workflow"]
    layout: Mapped[dict] = mapped_column(JSON, default=dict)
    is_dynamic: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
