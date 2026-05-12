"""
Purpose: DB model for defining User Roles (e.g., 'Sales Manager', 'Auditor').
Context: Part of Aras.Registry namespace. Level 3 implementation.
Impact: Enables advanced RBAC by grouping permissions into roles.
"""
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from ..base.model import Model

class Role(Model):
    """
    Groups permissions into manageable roles for users.
    """
    __tablename__ = "auth_roles"
    __title__ = "User Roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
