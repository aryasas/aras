from typing import Optional
from datetime import datetime
from sqlalchemy import String, ForeignKey, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from ..base.document import DocumentBase # DocumentBase for org_id and other common fields

class StockLayer(DocumentBase):
    __tablename__ = "erp_stock_layers"
    __features__ = ["audit"] # Stock layers should be auditable

    product_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_products.id"), nullable=False, index=True)
    qty_received: Mapped[float]
    qty_remaining: Mapped[float]
    unit_cost: Mapped[float]
    source_ref: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g. "GRN-001"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True) # Added for FIFO ordering
