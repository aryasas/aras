from typing import Optional
from datetime import date
from sqlalchemy import String, Date, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, object_session
from .erp_base import ErpBase

class DocumentBase(ErpBase):
    __abstract__ = True
    __features__ = ["audit", "workflow", "series"]
    __scoped_by__ = [("org_id", "erp_config_organizations")]

    org_id: Mapped[int] = mapped_column(ForeignKey("erp_config_organizations.id"), nullable=False, index=True)

    number: Mapped[str] = mapped_column(String(32), info={"read_only": True})
    doc_date: Mapped[date] = mapped_column(Date, default=date.today)
    status: Mapped[str] = mapped_column(
        String(20),
        default="Draft",
        info={"choices": ["Draft", "Confirmed", "Posted", "Cancelled"]},
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def before_save(self, is_new: bool):
        if is_new and not self.number:
            db = object_session(self)
            if db:
                from core.manager.naming_manager import NamingManager
                self.number = NamingManager.get_next(db, self.__tablename__)

DOC_LAYOUT_HEADER = {
    "key": "header",
    "title": "Header",
    "fields": ["number", "doc_date", "status", "org_id"],
}

DOC_LAYOUT_NOTES = {
    "key": "notes",
    "title": "Notes",
    "fields": ["notes"],
}
