from typing import Optional
from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from apps.base import ErpBase

class Note(ErpBase):
    __tablename__ = "erp_core_notes"
    __features__ = ["audit"]

    resource: Mapped[str] = mapped_column(String(100))   # e.g. "erp_accounting_inflow_invoices"
    record_id: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    tagged_users: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # comma-separated user IDs
