from typing import Optional
from sqlalchemy import String, ForeignKey, Float, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pydantic import BaseModel as PydanticBaseModel
from core import Aras
from core.response import ok
from apps.base import DocumentBase, LineItemBase, ErpBase


class PotTerminal(ErpBase):
    __tablename__ = "erp_pot_terminals"

    name: Mapped[str] = mapped_column(String(100))
    terminal_label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_stock_locations.id"), nullable=True)
    selling_pricelist_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_config_price_types.id"), nullable=True)
    allow_discount: Mapped[bool] = mapped_column(Boolean, default=True)
    receipt_header: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    receipt_footer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PotSession(DocumentBase):
    __tablename__ = "erp_pot_sessions"

    terminal_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_pot_terminals.id"), nullable=True)
    opening_balance: Mapped[float] = mapped_column(Float, default=0)
    closing_balance: Mapped[float] = mapped_column(Float, default=0)
    mode: Mapped[str] = mapped_column(String(20), default="sales", info={"choices": ["sales", "purchase", "both"]})

    @Aras.computed_field
    def total_sales(self) -> float:
        from apps.accounting.models import InflowInvoice, InflowInvoiceLine
        from sqlalchemy import func, select
        from sqlalchemy.orm import object_session
        db = object_session(self)
        if not db: return 0.0
        stmt = (
            select(func.sum(InflowInvoiceLine.qty * (InflowInvoiceLine.unit_price - InflowInvoiceLine.discount)))
            .join(InflowInvoice, InflowInvoiceLine.invoice_id == InflowInvoice.id)
            .where(InflowInvoice.pos_session_id == self.id)
        )
        return db.scalar(stmt) or 0.0

    @Aras.computed_field
    def total_purchase(self) -> float:
        from apps.accounting.models import OutflowInvoice, OutflowInvoiceLine
        from sqlalchemy import func, select
        from sqlalchemy.orm import object_session
        db = object_session(self)
        if not db: return 0.0
        stmt = (
            select(func.sum(OutflowInvoiceLine.qty * (OutflowInvoiceLine.unit_price - OutflowInvoiceLine.discount)))
            .join(OutflowInvoice, OutflowInvoiceLine.invoice_id == OutflowInvoice.id)
            .where(OutflowInvoice.pos_session_id == self.id)
        )
        return db.scalar(stmt) or 0.0

    @Aras.computed_field
    def invoice_count(self) -> int:
        from apps.accounting.models import InflowInvoice, OutflowInvoice
        from sqlalchemy import func, select
        from sqlalchemy.orm import object_session
        db = object_session(self)
        if not db: return 0
        inflow = db.scalar(select(func.count(InflowInvoice.id)).where(InflowInvoice.pos_session_id == self.id)) or 0
        outflow = db.scalar(select(func.count(OutflowInvoice.id)).where(OutflowInvoice.pos_session_id == self.id)) or 0
        return inflow + outflow

    @Aras.computed_field
    def payment_summary(self) -> list:
        from apps.accounting.models import InflowInvoice, OutflowInvoice, Payment, PaymentAllocation
        from sqlalchemy import func, select
        from sqlalchemy.orm import object_session
        db = object_session(self)
        if not db: return []

        in_ids = db.scalars(select(InflowInvoice.id).where(InflowInvoice.pos_session_id == self.id)).all()
        out_ids = db.scalars(select(OutflowInvoice.id).where(OutflowInvoice.pos_session_id == self.id)).all()
        all_ids = list(in_ids) + list(out_ids)
        if not all_ids:
            return []

        stmt = (
            select(Payment.mode_of_payment_id, func.sum(PaymentAllocation.amount))
            .join(PaymentAllocation, Payment.id == PaymentAllocation.payment_id)
            .where(PaymentAllocation.invoice_id.in_(all_ids))
            .group_by(Payment.mode_of_payment_id)
        )
        rows = db.execute(stmt).all()

        from apps.config.models import ModeOfPayment
        summary = []
        for mode_id, total in rows:
            mode_obj = db.get(ModeOfPayment, mode_id)
            summary.append({"mode_name": mode_obj.name if mode_obj else "Unknown", "total_amount": float(total)})
        return summary

    class _CloseSessionInput(PydanticBaseModel):
        closing_balance: float = 0.0

    @Aras.model_action(name="open_pos", permission="edit", label="Open POS")
    def open_pos(self, db):
        return ok({"redirect": f"/erp/pot/sessions/{self.id}/pos"}, message="")

    @Aras.model_action(name="close_session", permission="edit", label="Close Session", input_schema=_CloseSessionInput)
    def close_session(self, db, data: _CloseSessionInput):
        self.closing_balance = data.closing_balance
        self.status = "Posted"
        return ok({"status": self.status}, message="POT Session closed successfully.")

    @Aras.model_action(name="shift_report", permission="read", label="Shift Report")
    def shift_report(self, db):
        from sqlalchemy.orm import object_session
        s = object_session(self)
        return ok({
            "session_id": self.id,
            "session_number": self.number,
            "status": self.status,
            "total_sales": self.total_sales,
            "total_purchase": self.total_purchase,
            "invoice_count": self.invoice_count,
            "payment_summary": self.payment_summary,
            "opening_balance": float(self.opening_balance or 0),
            "closing_balance": float(self.closing_balance or 0),
        }, message="Shift Report")
