from typing import Dict, Any
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ..base.model import Model
from ..auth.models import User

class DashboardLayoutModel(Model):
    """
    Registry for user-specific dashboard layouts and configurations.
    """
    __tablename__ = "core_dashboard_layouts"
    __hidden__ = True

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(User.id, ondelete="CASCADE"), nullable=False)
    user: Mapped[User] = relationship(User, backref="dashboard_layouts")

    layout_config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True, default=lambda: {}) # Stores grid layout and widget instances

    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    
    __table_args__ = (
        # A user can only have one default dashboard
        # UniqueConstraint(user_id, is_default, name='_user_default_dashboard_uc'),
    )
