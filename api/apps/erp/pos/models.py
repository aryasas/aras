from sqlalchemy import String, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base import DocumentBase, LineItemBase

class PosSession(DocumentBase):
    __tablename__ = "erp_pos_sessions"
    opening_balance: Mapped[float] = mapped_column(Float, default=0)
    closing_balance: Mapped[float] = mapped_column(Float, default=0)

    orders: Mapped[list["PosOrder"]] = relationship("PosOrder", back_populates="session", cascade="all, delete-orphan")

class PosOrder(DocumentBase):
    __tablename__ = "erp_pos_orders"
    __parent__ = "erp_pos_sessions"
    session_id: Mapped[int] = mapped_column(ForeignKey("erp_pos_sessions.id"))
    customer_id: Mapped[int] = mapped_column(ForeignKey("erp_crm_customers.id"), nullable=True)
    pricelist_id: Mapped[int] = mapped_column(ForeignKey("erp_config_price_types.id"), nullable=True)

    lines: Mapped[list["PosOrderLine"]] = relationship("PosOrderLine", back_populates="parent", cascade="all, delete-orphan")
    session: Mapped["PosSession"] = relationship("PosSession", back_populates="orders")

class PosOrderLine(LineItemBase):
    __tablename__ = "erp_pos_order_lines"
    __parent__ = "erp_pos_orders"
    order_id: Mapped[int] = mapped_column(ForeignKey("erp_pos_orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_products.id"))
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    uom_id: Mapped[int] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)
    price: Mapped[float] = mapped_column(Float, default=0)
    discount: Mapped[float] = mapped_column(Float, default=0)

    parent: Mapped["PosOrder"] = relationship("PosOrder", back_populates="lines")
