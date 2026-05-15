"""
Purpose: DB model for defining User Roles (e.g., 'Sales Manager', 'Auditor').
Context: Part of Aras.Registry namespace. Level 3 implementation.
Impact: Enables advanced RBAC by grouping permissions into roles.
"""
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from ..base.model import Model
from ..base.field import Field

class Role(Model):
    """
    Groups permissions into manageable roles for users.
    """
    __tablename__ = "auth_roles"
    __features__ = []

    name: Mapped[str] = Field(String(50), unique=True, index=True, label="Role Name")
    description: Mapped[str] = Field(String(255), nullable=True, label="Description")
