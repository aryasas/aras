# claude-sonnet-4-6
"""
AppConfig — typed, per-organization configuration base owned by each app.

Why typed (not key-value): most app config carries FK integrity (e.g. an
accounting default account must point at a real accounting_accounts row).
A key-value store would replace DB FK constraints with stringly-typed JSON —
strictly worse for financial config. So each app subclasses AppConfig with
real columns and a real table, registered by key via AppConfigRegistry.

org_id targets the framework-owned organization table. (core_organizations
is framework after the tenant move; until then the string still resolves.)
"""
from typing import ClassVar
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from core import Aras


class AppConfig(Aras.Model):
    __abstract__ = True
    __features__ = ["audit"]

    # app_name key the framework registers this config under. Subclasses set it.
    __config_for__: ClassVar[str] = ""

    org_id: Mapped[int] = mapped_column(
        ForeignKey("core_organizations.id"), index=True
    )
