from sqlalchemy import String, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from apps.erp.base.document import DocumentBase

class StockLayer(DocumentBase):
    __tablename__ = "erp_stock_layers"
    product_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_products.id"))
    qty_received: Mapped[float] = mapped_column(Float)
    qty_remaining: Mapped[float] = mapped_column(Float)
    unit_cost: Mapped[float] = mapped_column(Float)
    source_ref: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # e.g. "GRN-001"