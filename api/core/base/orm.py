# claude-opus-4-8
"""Framework-tier abstract ORM bases.

Domain-agnostic SQLAlchemy bases shared by every app, plugin, and core/workspace
model. They live in core/ (not apps/) because they carry zero business coupling —
only audit/soft-delete/scoping plumbing — and both plugins and apps depend on them.
Keeping them here preserves the tier rule: core never imports apps/ or plugins/.

The org/currency tablenames referenced here (core_organizations, etc.) are owned
by core.workspace, which is also framework tier — so no upward dependency exists.
"""
from typing import Optional
from datetime import date
from sqlalchemy import String, Integer, ForeignKey, Boolean, Float, Date, func
from sqlalchemy.orm import Mapped, mapped_column
from core import Aras


class AuditedBase(Aras.Model):
    __abstract__ = True
    __features__ = ["audit"]


class ConfigBase(AuditedBase):
    __abstract__ = True
    __features__ = ["audit"]
    name: Mapped[str] = mapped_column(String(200))


class LineItemBase(AuditedBase):
    __abstract__ = True
    __features__ = ["audit"]
    sequence: Mapped[int] = mapped_column(Integer, default=0, info={"hidden": True})
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    qty: Mapped[float] = mapped_column(Float, default=0)
    amount: Mapped[float] = mapped_column(Float, default=0)


class MasterDataBase(AuditedBase):
    __abstract__ = True
    __soft_delete__ = True
    __features__ = ["audit"]
    __scoped_by__ = [("org_id", "core_organizations")]

    org_id: Mapped[int] = mapped_column(Integer, ForeignKey("core_organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200))
    is_shared: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)


class DocumentBase(AuditedBase):
    __abstract__ = True
    __features__ = ["audit", "workflow", "series"]
    __scoped_by__ = [("org_id", "core_organizations")]

    org_id: Mapped[int] = mapped_column(ForeignKey("core_organizations.id"), nullable=False, index=True)

    number: Mapped[str] = mapped_column(String(32), info={"read_only": True})
    
    # claude-sonnet-4-6: Using server-side date for UTC compliance
    doc_date: Mapped[date] = mapped_column(Date, default=func.current_date())
    
    status: Mapped[str] = mapped_column(
        String(20),
        default="Draft",
        info={"choices": ["Draft", "Confirmed", "Posted", "Cancelled"]},
    )
    note_id: Mapped[Optional[int]] = mapped_column(ForeignKey("core_notes.id"), nullable=True)

    def before_save(self, is_new: bool, db=None):
        if not self.number and db is not None:
            from core.lib.numbering import SeriesManager
            self.number = SeriesManager.get_next(db, self.__tablename__)


DOC_LAYOUT_HEADER = {
    "key": "header",
    "title": "Header",
    "fields": ["number", "doc_date", "status", "org_id"],
}

DOC_LAYOUT_NOTES = {
    "key": "notes",
    "title": "Notes",
    "fields": ["note_id"],
}
