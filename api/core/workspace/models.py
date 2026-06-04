# claude-opus-4-8
"""Workspace primitives — domain-agnostic, framework-tier.

Organization is a neutral tenant/company entity usable by SaaS *and* custom
(non-SaaS) products, so it lives here rather than in core/tenant. Product-specific
behaviour (accounting COA mirror, report seeding on create) is attached app-side
via model-action monkey-attach + SQLAlchemy event listeners — keeping this module
free of any apps/* import (framework purity invariant).

Tablenames now use the framework-owned core_* prefix.
"""
from typing import Optional
from sqlalchemy import String, ForeignKey, Text, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base.field import Field
from .base import WorkspaceConfigBase as ConfigBase, WorkspaceMasterDataBase as MasterDataBase


# claude-opus-4-8
# Canonical org unit-type options — single source consumed by the unit_type_picker
# combobox via GET /config/unit-types. Static (no DB), so no migration.
UNIT_TYPE_OPTIONS: list[dict[str, str]] = [
    {"key": "organization", "label": "Organization"},
    {"key": "group", "label": "Group"},
    {"key": "branch", "label": "Branch"},
    {"key": "outlet", "label": "Outlet"},
    {"key": "warehouse", "label": "Warehouse"},
]


class Organization(ConfigBase):
    __tablename__ = "core_organizations"

    code: Mapped[str] = mapped_column(String(50), unique=True)
    profile: Mapped[str] = Field(String(50), default="general", ui_type="profile_picker", label="Profile")
    unit_type: Mapped[str] = Field(String(50), default="organization", ui_type="unit_type_picker", label="Unit Type")

    # Multi-company / group structure
    is_group: Mapped[bool] = mapped_column(Boolean, default=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("core_organizations.id"), nullable=True)

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
    base_currency_id: Mapped[Optional[int]] = mapped_column(ForeignKey("core_currencies.id"), nullable=True)
    fiscal_year_start_month: Mapped[int] = mapped_column(Integer, default=1)
    # Accounting defaults + inventory flags live in accounting.AccountingConfig /
    # stock.StockConfig — read via AppConfigRegistry.get(db, "accounting"|"stock", org_id).

    # If set, account comboboxes use this org's COA instead of own (branch sharing parent ledger)
    coa_source_org_id: Mapped[Optional[int]] = mapped_column(ForeignKey("core_organizations.id"), nullable=True)

    # Relationships
    parent: Mapped[Optional["Organization"]] = relationship("Organization", foreign_keys=[parent_id], remote_side="Organization.id", backref="children")
    coa_source_org: Mapped[Optional["Organization"]] = relationship("Organization", foreign_keys=[coa_source_org_id])


class Currency(ConfigBase):
    __tablename__ = "core_currencies"
    code: Mapped[str] = mapped_column(String(10), unique=True)
    symbol: Mapped[str] = mapped_column(String(10))


class PrintTemplate(MasterDataBase):
    __tablename__ = "core_print_templates"

    doc_type: Mapped[str] = mapped_column(String(50))
    code: Mapped[str] = mapped_column(String(50))
    engine: Mapped[str] = mapped_column(String(20), default="jinja")
    body_html: Mapped[str] = mapped_column(Text)
    header_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    footer_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    css: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(default=False)


class Notification(MasterDataBase):
    __tablename__ = "core_notifications"

    user_id: Mapped[int] = mapped_column(ForeignKey("core_users.id"))
    type: Mapped[str] = mapped_column(String(50))
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_read: Mapped[bool] = mapped_column(default=False)
