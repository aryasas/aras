"""
Purpose: DB model for granular permission mapping (Resource + Action).
Context: Part of Aras.Registry namespace. Level 3 implementation.
Impact: The engine's security truth table for data-level access.
"""
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped
from ..base.model import Model
from ..base.field import Field

class Permission(Model):
    """
    Maps Roles to specific Resources and Actions.
    Example: Role 'Sales' can 'UPDATE' resource 'accounting_inflow_invoices'.
    """
    __tablename__ = "core_permissions"
    __features__ = []

    role_id: Mapped[int] = Field(ForeignKey("core_roles.id"), label="Role", display_column="name")
    resource: Mapped[str] = Field(String(100), label="Resource Name")
    action: Mapped[str] = Field(String(20), label="Action")
