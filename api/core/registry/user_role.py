"""
Purpose: Bridge table linking Users to Roles.
Context: Part of Aras.Registry namespace. Level 3 implementation.
Impact: Enables many-to-many relationship between users and roles.
"""
from typing import Optional
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from ..base.model import Model

class UserRole(Model):
    """
    Assigns one or more roles to a user.
    """
    __tablename__ = "auth_user_roles"

    user_id: Mapped[int] = mapped_column(ForeignKey("auth_users.id"))
    role_id: Mapped[int] = mapped_column(ForeignKey("auth_roles.id"))
    # Soft FK to erp_config_organizations — no hard constraint to avoid cross-schema
    # ordering issues in SQLite tests; enforced at application layer.
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)

