from typing import Optional
from sqlalchemy import String, ForeignKey, Float, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core import Aras
from ..base import DocumentBase, LineItemBase


class PosTerminal(LineItemBase):
    __tablename__ = "erp_pos_terminals"

    name: Mapped[str] = mapped_column(String(100))
    warehouse_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_stock_warehouses.id"), nullable=True)
    selling_pricelist_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_config_price_types.id"), nullable=True)
    allow_discount: Mapped[bool] = mapped_column(Boolean, default=True)
    receipt_header: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    receipt_footer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PosSession(DocumentBase):
    __tablename__ = "erp_pos_sessions"

    terminal_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_pos_terminals.id"), nullable=True)
    opening_balance: Mapped[float] = mapped_column(Float, default=0)
    closing_balance: Mapped[float] = mapped_column(Float, default=0)

    orders: Mapped[list["PosOrder"]] = relationship("PosOrder", back_populates="session", cascade="all, delete-orphan")

    @Aras.model_action(name="get_products", permission="read", label="POS Products")
    def get_products(self):
        from .services.pos import PosService
        from sqlalchemy.orm import object_session
        db = object_session(self)
        return PosService.get_pos_products(db, self.id)

    @Aras.model_action(name="submit_order", permission="edit", label="Submit POS Order")
    def submit_order(self, data: dict):
        from .services.pos import PosService
        from sqlalchemy.orm import object_session
        db = object_session(self)
        return PosService.process_order(db, self.id, data)

    @Aras.model_action(name="close_session", permission="edit", label="Close Session")
    def close_session(self, data: dict):
        from .services.pos import PosService
        from sqlalchemy.orm import object_session
        db = object_session(self)
        cash_counted = data.get("cash_counted", 0)
        return PosService.close_session(db, self.id, cash_counted)

    @Aras.model_action(name="shift_report", permission="read", label="Shift Report")
    def shift_report(self):
        from .services.pos import PosService
        from sqlalchemy.orm import object_session
        db = object_session(self)
        return PosService.get_shift_report(db, self.id)


class PosOrder(DocumentBase):
    __tablename__ = "erp_pos_orders"
    __parent__ = "erp_pos_sessions"

    session_id: Mapped[int] = mapped_column(ForeignKey("erp_pos_sessions.id"))
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_crm_customers.id"), nullable=True)
    pricelist_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_config_price_types.id"), nullable=True)
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    paid_amount: Mapped[float] = mapped_column(Float, default=0)
    change_amount: Mapped[float] = mapped_column(Float, default=0)

    lines: Mapped[list["PosOrderLine"]] = relationship("PosOrderLine", back_populates="parent", cascade="all, delete-orphan")
    payments: Mapped[list["PosPaymentLine"]] = relationship("PosPaymentLine", back_populates="parent", cascade="all, delete-orphan")
    session: Mapped["PosSession"] = relationship("PosSession", back_populates="orders")


class PosOrderLine(LineItemBase):
    __tablename__ = "erp_pos_order_lines"
    __parent__ = "erp_pos_orders"

    order_id: Mapped[int] = mapped_column(ForeignKey("erp_pos_orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("erp_stock_products.id"))
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    uom_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_config_uoms.id"), nullable=True)
    price: Mapped[float] = mapped_column(Float, default=0)
    discount: Mapped[float] = mapped_column(Float, default=0)

    parent: Mapped["PosOrder"] = relationship("PosOrder", back_populates="lines")


class PosPaymentLine(LineItemBase):
    __tablename__ = "erp_pos_payment_lines"
    __parent__ = "erp_pos_orders"

    order_id: Mapped[int] = mapped_column(ForeignKey("erp_pos_orders.id"))
    mode_id: Mapped[int] = mapped_column(ForeignKey("erp_config_payment_modes.id"))
    amount: Mapped[float] = mapped_column(Float, default=0)

    parent: Mapped["PosOrder"] = relationship("PosOrder", back_populates="payments")
