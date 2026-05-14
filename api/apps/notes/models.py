from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from core import Aras

class Note(Aras.Model):
    __tablename__ = "notes_note"
    __features__ = ["audit"]
    __title__ = "Notes"
    __searchable_fields__ = ["title", "body"]
    __display_fields__ = ("title",)

    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, nullable=True)