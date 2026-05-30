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
    __tablename__ = "core_user_roles"

    user_id: Mapped[int] = mapped_column(ForeignKey("core_users.id"))
    role_id: Mapped[int] = mapped_column(ForeignKey("core_roles.id"))


