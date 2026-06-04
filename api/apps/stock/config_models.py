# claude-sonnet-4-6
"""
StockConfig — per-organization inventory settings, owned by the stock app.

The inventory flags (valuation method, perpetual mode, zero-stock policy) and the
stock-specific GL accounts lived on Organization, coupling the tenant identity to
inventory mechanics. Moved here so stock owns them; accounting/framework read via
the AppConfigRegistry only when stock is installed.
"""
from typing import Optional
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from core.config import AppConfig

_ACC_FK = {"fk_filter": {"org_id": "org_id"}}


class StockConfig(AppConfig):
    __tablename__ = "stock_config"
    __config_for__ = "stock"

    _ACC_FIELDS = [
        "acc_stock_received_not_billed_id", "acc_stock_provisional_id",
        "acc_stock_adjustment_id", "acc_expenses_in_valuation_id", "acc_stock_default_id",
    ]

    # Inventory behaviour flags (moved from Organization)
    enable_perpetual_inventory: Mapped[bool] = mapped_column(default=False)
    enable_provisional_non_stock: Mapped[bool] = mapped_column(default=False)
    avg_cost_by_location: Mapped[bool] = mapped_column(default=False)
    allow_zero_stock: Mapped[bool] = mapped_column(default=False)
    stock_valuation_method: Mapped[str] = mapped_column(String(10), default="FIFO", info={"choices": ["FIFO", "AVERAGE"]})

    # Stock / Inventory GL accounts
    acc_stock_received_not_billed_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_stock_provisional_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_stock_adjustment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_expenses_in_valuation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_stock_default_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
