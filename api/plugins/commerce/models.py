# claude-sonnet-4-6
"""
Commerce primitives moved out of apps/settings so they're reusable across products
without coupling to the ERP "config" app. Tablenames keep their config_* prefix
to preserve the existing schema (rename is a separate, later phase).

These are nouns (units, charges, rates) — not engines. Engines that act on them
(journal posting, valuation) stay in their owning apps and resolve these by FK.
"""
from datetime import date
from typing import Optional
from sqlalchemy import String, ForeignKey, Float, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.base.orm import ConfigBase, MasterDataBase, LineItemBase


class Uom(ConfigBase):
    __tablename__ = "config_uoms"


class PriceType(ConfigBase):
    __tablename__ = "config_price_types"
    kind: Mapped[str] = mapped_column(String(20), default="sales")  # sales or purchase


class Charge(ConfigBase):
    __tablename__ = "config_charges"

    charge_type: Mapped[str] = mapped_column(String(20), default="Both", info={"choices": ["Sales", "Purchase", "Both"]})
    calc_method: Mapped[str] = mapped_column(String(10), default="Percent", info={"choices": ["Percent", "Fixed"]})
    rate: Mapped[float] = mapped_column(default=0)
    amount: Mapped[float] = mapped_column(default=0)
    is_inclusive: Mapped[bool] = mapped_column(default=False)
    is_compound: Mapped[bool] = mapped_column(default=False)
    sequence: Mapped[int] = mapped_column(default=10, info={"hidden": True})

    account_collected_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True)
    account_paid_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True)


class ExchangeRate(MasterDataBase):
    __tablename__ = "config_exchange_rates"

    currency_id: Mapped[int] = mapped_column(ForeignKey("core_currencies.id"))
    rate: Mapped[float] = mapped_column(Float)
    rate_date: Mapped[date] = mapped_column(Date)


class ModeOfPayment(MasterDataBase):
    __tablename__ = "config_payment_modes"

    payment_type: Mapped[str] = mapped_column(String(20), default="Cash", info={"choices": ["Cash", "Bank", "E-Wallet", "Other"]})

    accounts: Mapped[list["OrganizationPaymentAccount"]] = relationship("OrganizationPaymentAccount", back_populates="parent", cascade="all, delete-orphan")


class OrganizationPaymentAccount(LineItemBase):
    __tablename__ = "config_payment_accounts"
    __parent__ = "config_payment_modes"

    mode_id: Mapped[int] = mapped_column(ForeignKey("config_payment_modes.id"))
    account_id: Mapped[int] = mapped_column(ForeignKey("accounting_accounts.id"), info={"display_column": "display_name"})

    parent: Mapped["ModeOfPayment"] = relationship("ModeOfPayment", back_populates="accounts")
