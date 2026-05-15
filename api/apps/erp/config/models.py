from datetime import date
from typing import Optional
from sqlalchemy import String, ForeignKey, Float, Date, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base import ConfigBase, MasterDataBase, LineItemBase

class Company(MasterDataBase):
    __tablename__ = "erp_config_companies"
    __scoped_by__ = [] 

class Currency(ConfigBase):
    __tablename__ = "erp_config_currencies"
    symbol: Mapped[str] = mapped_column(String(10))

class Uom(ConfigBase):
    __tablename__ = "erp_config_uoms"

class PriceType(ConfigBase):
    __tablename__ = "erp_config_price_types"
    kind: Mapped[str] = mapped_column(String(20), default="sales") # sales or purchase


class Charge(ConfigBase):
    __tablename__ = "erp_config_charges"
    
    charge_type: Mapped[str] = mapped_column(String(20), default="Both", info={"choices": ["Sales", "Purchase", "Both"]})
    calc_method: Mapped[str] = mapped_column(String(10), default="Percent", info={"choices": ["Percent", "Fixed"]})
    rate: Mapped[float] = mapped_column(default=0)
    amount: Mapped[float] = mapped_column(default=0)
    is_inclusive: Mapped[bool] = mapped_column(default=False)
    is_compound: Mapped[bool] = mapped_column(default=False)
    sequence: Mapped[int] = mapped_column(default=10)
    
    account_collected_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    account_paid_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)


class ExchangeRate(MasterDataBase):
    __tablename__ = "erp_config_exchange_rates"

    currency_id: Mapped[int] = mapped_column(ForeignKey("erp_config_currencies.id"))
    rate: Mapped[float] = mapped_column(Float)
    rate_date: Mapped[date] = mapped_column(Date)


class Setting(MasterDataBase):
    __tablename__ = "erp_config_settings"
    __scoped_by__ = []

    key: Mapped[str] = mapped_column(String(200), unique=True)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    value_type: Mapped[str] = mapped_column(String(20), default="str", info={"choices": ["str", "int", "float", "bool", "json"]})
    group: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ModeOfPayment(MasterDataBase):
    __tablename__ = "erp_config_payment_modes"
    
    payment_type: Mapped[str] = mapped_column(String(20), default="Cash", info={"choices": ["Cash", "Bank", "E-Wallet", "Other"]})
    
    accounts: Mapped[list["CompanyPaymentAccount"]] = relationship("CompanyPaymentAccount", back_populates="parent", cascade="all, delete-orphan")


class CompanyPaymentAccount(LineItemBase):
    __tablename__ = "erp_config_payment_accounts"
    __parent__ = "erp_config_payment_modes"
    
    mode_id: Mapped[int] = mapped_column(ForeignKey("erp_config_payment_modes.id"))
    account_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_accounts.id"))
    
    parent: Mapped["ModeOfPayment"] = relationship("ModeOfPayment", back_populates="accounts")


class PrintTemplate(MasterDataBase):
    __tablename__ = "erp_config_print_templates"
    
    doc_type: Mapped[str] = mapped_column(String(50))
    code: Mapped[str] = mapped_column(String(50))
    engine: Mapped[str] = mapped_column(String(20), default="jinja")
    body_html: Mapped[str] = mapped_column(Text)
    header_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    footer_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    css: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(default=False)


class Report(MasterDataBase):
    __tablename__ = "erp_config_reports"
    
    report_type: Mapped[str] = mapped_column(String(20), default="query", info={"choices": ["Query", "Script", "Jinja"]})
    module: Mapped[str] = mapped_column(String(50), default="General")
    columns_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    filters_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    script: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    linked_doctype: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class Notification(MasterDataBase):
    __tablename__ = "erp_config_notifications"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("auth_users.id"))
    type: Mapped[str] = mapped_column(String(50))
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_read: Mapped[bool] = mapped_column(default=False)

