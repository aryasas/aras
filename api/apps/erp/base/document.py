from typing import Optional
from datetime import date
from sqlalchemy import String, Date, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, object_session
from core import Aras

class DocumentBase(Aras.Model):
    __abstract__ = True
    __features__ = ["audit", "workflow", "scoped"]
    __scoped_by__ = [("company_id", "erp_config_companies")]

    number: Mapped[str] = mapped_column(String(32), info={"form_hidden": True})
    doc_date: Mapped[date] = mapped_column(Date, default=date.today)
    status: Mapped[str] = mapped_column(
        String(20),
        default="Draft",
        info={"choices": ["Draft", "Confirmed", "Posted", "Cancelled"]},
    )
    currency_id: Mapped[int] = mapped_column(ForeignKey("erp_config_currencies.id"))
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def before_save(self, is_new: bool):
        if is_new and not self.number:
            db = object_session(self)
            if db:
                from core.manager.naming_manager import NamingManager
                self.number = NamingManager.get_next(db, self.__tablename__)
