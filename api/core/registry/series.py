"""
Purpose: Core registry for sequential document numbering (Series).
Context: Part of Aras.Registry namespace.
Impact: Enables automatic, formatted ID generation for models (e.g., INV-2026-0001).
"""
from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from ..base.model import Model

class Series(Model):
    """Stores sequential counters and formats for document numbering."""
    __tablename__ = "core_series"
    __features__ = []

    key: Mapped[str] = mapped_column(String(100), unique=True, index=True) # e.g. "stock_movements"
    prefix: Mapped[str] = mapped_column(String(50), nullable=True) # e.g. "MV-"
    format: Mapped[str] = mapped_column(String(100), default="{prefix}{year}{next_value:04d}")
    next_value: Mapped[int] = mapped_column(Integer, default=1)
    last_reset_year: Mapped[int] = mapped_column(Integer, nullable=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
