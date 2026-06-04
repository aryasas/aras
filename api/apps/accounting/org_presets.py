# claude-opus-4-8
"""Per-org accounting presets: domain vocabulary + posting rules.

Relocated from apps/settings — these are accounting-domain concepts (posting rules
FK accounting_accounts; vocabulary drives accounting document labels). Tablenames
follow the accounting_* app prefix.
"""
from typing import Optional
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.base.orm import ConfigBase


class OrganizationVocabulary(ConfigBase):
    __tablename__ = "accounting_org_vocabulary"
    org_id: Mapped[int] = mapped_column(ForeignKey("core_organizations.id"))
    key: Mapped[str] = mapped_column(String(50))
    label: Mapped[str] = mapped_column(String(100))


class OrganizationPostingRule(ConfigBase):
    __tablename__ = "accounting_org_posting_rules"
    org_id: Mapped[int] = mapped_column(ForeignKey("core_organizations.id"))
    trx_type: Mapped[str] = mapped_column(String(50))
    debit_account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True)
    credit_account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
