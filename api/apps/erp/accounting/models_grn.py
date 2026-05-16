from typing import Optional
from sqlalchemy import String, Integer, Float, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base import LineItemBase
from core import Aras

class GoodsReceiptLine(LineItemBase):
    __tablename__ = "erp_accounting_grn_lines"
    __parent__ = "erp_accounting_grns"

    grn_id: Mapped[int] = mapped_column(ForeignKey("erp_accounting_grns.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_products.id"))
    quantity_received: Mapped[float] = mapped_column(Numeric, default=0)
    unit_cost: Mapped[float] = mapped_column(Numeric, default=0)

    parent: Mapped["GoodsReceiptNote"] = relationship("GoodsReceiptNote", back_populates="lines")
