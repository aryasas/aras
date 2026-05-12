"""
Purpose: DB model for granular permission mapping (Resource + Action).
Context: Part of Aras.Registry namespace. Level 3 implementation.
Impact: The engine's security truth table for data-level access.
"""
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..base.model import Model

class Permission(Model):
    """
    Maps Roles to specific Resources and Actions.
    Example: Role 'Sales' can 'UPDATE' resource 'erp_invoices'.
    """
    __tablename__ = "auth_permissions"
    __title__ = "Data Permissions"

    role_id: Mapped[int] = mapped_column(ForeignKey("auth_roles.id"))
    resource: Mapped[str] = mapped_column(String(100)) # e.g. "erp_invoices"
    action: Mapped[str] = mapped_column(String(20))   # e.g. "READ", "CREATE", "UPDATE", "DELETE", "TRANSITION"
