"""
Purpose: Bridge table linking Users to Roles.
Context: Part of Aras.Registry namespace. Level 3 implementation.
Impact: Enables many-to-many relationship between users and roles.
"""
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..base.model import Model

class UserRole(Model):
    """
    Assigns one or more roles to a user.
    """
    __tablename__ = "auth_user_roles"
    __title__ = "User-Role Mapping"

    user_id: Mapped[int] = mapped_column(ForeignKey("auth_users.id"))
    role_id: Mapped[int] = mapped_column(ForeignKey("auth_roles.id"))
