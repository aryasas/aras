from datetime import date
from typing import Optional
from sqlalchemy import String, ForeignKey, Float, Date, Text, JSON, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base import ConfigBase, MasterDataBase, LineItemBase

class Organization(ConfigBase):
    __tablename__ = "erp_config_organizations"

    profile: Mapped[str] = mapped_column(String(50), default="general")
    unit_type: Mapped[str] = mapped_column(String(50), default="organization")

    # Multi-company / group structure
    is_group: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_config_organizations.id"), nullable=True)

    # Identity & Details
    legal_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    trade_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    logo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Configuration
    base_currency_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_config_currencies.id"), nullable=True)
    fiscal_year_start_month: Mapped[int] = mapped_column(Integer, default=1)
    default_coa_template: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    default_charge_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_config_charges.id"), nullable=True)
    default_charge_enable: Mapped[bool] = mapped_column(Boolean, default=False)

    # Accounting mode
    enable_perpetual_inventory: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_provisional_non_stock: Mapped[bool] = mapped_column(Boolean, default=False)
    avg_cost_by_location: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_zero_stock: Mapped[bool] = mapped_column(Boolean, default=False)

    # Default Accounts
    acc_bank_default_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    acc_cash_default_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    acc_receivable_default_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    acc_payable_default_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    acc_income_default_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    acc_cogs_default_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    acc_inventory_default_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    acc_payroll_payable_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    acc_payment_discount_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    acc_write_off_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    acc_unrealized_gain_loss_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    acc_round_off_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    
    # Stock / Inventory Accounts
    acc_stock_received_not_billed_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    acc_stock_provisional_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    acc_stock_adjustment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    acc_expenses_in_valuation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    acc_stock_default_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)

    # Tax accounts
    acc_tax_output_ppn_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    acc_tax_input_ppn_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    
    # Formatting Defaults
    date_format: Mapped[str] = mapped_column(String(20), default="DD/MM/YYYY")
    number_format: Mapped[str] = mapped_column(String(20), default="#,###.##")
    decimal_precision: Mapped[int] = mapped_column(Integer, default=2)

    # Relationships
    parent: Mapped[Optional["Organization"]] = relationship("Organization", remote_side="Organization.id", backref="children")

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


class Setting(ConfigBase):
    __tablename__ = "erp_config_settings"

    key: Mapped[str] = mapped_column(String(200), unique=True)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    value_type: Mapped[str] = mapped_column(String(20), default="str", info={"choices": ["str", "int", "float", "bool", "json"]})
    group: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ModeOfPayment(MasterDataBase):
    __tablename__ = "erp_config_payment_modes"
    
    payment_type: Mapped[str] = mapped_column(String(20), default="Cash", info={"choices": ["Cash", "Bank", "E-Wallet", "Other"]})
    
    accounts: Mapped[list["OrganizationPaymentAccount"]] = relationship("OrganizationPaymentAccount", back_populates="parent", cascade="all, delete-orphan")


class OrganizationPaymentAccount(LineItemBase):
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


class Notification(MasterDataBase):
    __tablename__ = "erp_config_notifications"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("auth_users.id"))
    type: Mapped[str] = mapped_column(String(50))
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_read: Mapped[bool] = mapped_column(default=False)


class OrganizationVocabulary(ConfigBase):
    __tablename__ = "erp_config_org_vocabulary"
    org_id: Mapped[int] = mapped_column(ForeignKey("erp_config_organizations.id"))
    key: Mapped[str] = mapped_column(String(50))
    label: Mapped[str] = mapped_column(String(100))

class OrganizationPostingRule(ConfigBase):
    __tablename__ = "erp_config_org_posting_rules"
    org_id: Mapped[int] = mapped_column(ForeignKey("erp_config_organizations.id"))
    trx_type: Mapped[str] = mapped_column(String(50))
    debit_account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    credit_account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_accounting_accounts.id"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

