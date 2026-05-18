from typing import Optional
from sqlalchemy import String, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from .erp_base import ErpBase

class LineItemBase(ErpBase):
    __abstract__ = True
    __features__ = ["audit"]
    sequence: Mapped[int] = mapped_column(Integer, default=0, info={"hidden": True})
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    qty: Mapped[float] = mapped_column(Float, default=0)
    amount: Mapped[float] = mapped_column(Float, default=0)
