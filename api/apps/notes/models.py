from typing import Optional
from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from core import Aras
from core.base.orm import AuditedBase

class Note(Aras.Model):
    __tablename__ = "notes_note"
    __features__ = ["audit"]
    __searchable_fields__ = ["title", "body"]
    __display_fields__ = ("title",)

    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, nullable=True)


# Moved from the orphan apps/app_core (which had no app.py, so core_notes was
# never mapped despite apps/base/document.py holding an FK to it). Tablename
# preserved — no schema change.
class DocumentNote(AuditedBase):
    __tablename__ = "core_notes"
    __features__ = ["audit"]

    resource: Mapped[str] = mapped_column(String(100))   # e.g. "accounting_inflow_invoices"
    record_id: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    tagged_users: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # comma-separated user IDs