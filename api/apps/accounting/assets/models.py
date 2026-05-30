from typing import Optional
from datetime import date
from sqlalchemy import String, ForeignKey, Date, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column
from apps.base import MasterDataBase

class AssetCategory(MasterDataBase):
    __tablename__ = "accounting_assets_categories"
    depreciation_method: Mapped[str] = mapped_column(String(50), default="straight_line")
    useful_life_years: Mapped[int] = mapped_column(Integer, default=5)

class Asset(MasterDataBase):
    __tablename__ = "accounting_assets_assets"
    category_id: Mapped[int] = mapped_column(ForeignKey("accounting_assets_categories.id"))
    purchase_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    purchase_value: Mapped[float] = mapped_column(Float, default=0.0)
    current_value: Mapped[float] = mapped_column(Float, default=0.0)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")
