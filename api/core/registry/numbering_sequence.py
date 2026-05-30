# gemini-flash
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from ..base.model import Model

class NumberingSequence(Model):
    """Stores the last sequence number for various document types."""
    __tablename__ = "core_numbering_sequences"
    __unique_together__ = [("doc_type", "org_id", "year")]

    doc_type: Mapped[str] = mapped_column(String(100))
    org_id: Mapped[int] = mapped_column(Integer, default=0) # Isolation per company/org
    year: Mapped[int] = mapped_column(Integer, default=0)
    last_seq: Mapped[int] = mapped_column(Integer, default=0)
