from typing import Optional
from datetime import date
from sqlalchemy import String, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .erp_base import ErpBase

class DocumentBase(ErpBase):
    __abstract__ = True
    __features__ = ["audit", "workflow", "series"]
    __scoped_by__ = [("org_id", "config_organizations")]

    org_id: Mapped[int] = mapped_column(ForeignKey("config_organizations.id"), nullable=False, index=True)

    number: Mapped[str] = mapped_column(String(32), info={"read_only": True})
    doc_date: Mapped[date] = mapped_column(Date, default=date.today)
    status: Mapped[str] = mapped_column(
        String(20),
        default="Draft",
        info={"choices": ["Draft", "Confirmed", "Posted", "Cancelled"]},
    )
    note_id: Mapped[Optional[int]] = mapped_column(ForeignKey("core_notes.id"), nullable=True)

    def before_save(self, is_new: bool, db=None):
        if not self.number and db is not None:
            from core.manager.naming_manager import SeriesManager
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
