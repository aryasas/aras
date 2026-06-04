# gemini-flash
from typing import Optional, List
from sqlalchemy import String, ForeignKey, Float, Date, Integer
from sqlalchemy.orm import Mapped, mapped_column
from core import Aras, LinkedDoc
from core.response import ok
from core.exceptions import ValidationException
from core.base.orm import DocumentBase

class TradeDocumentBase(DocumentBase):
    """
    Base class for Inflow (Sales) and Outflow (Purchase) invoices/orders.
    Consolidates shared columns, computed fields, and workflow logic.
    """
    __abstract__ = True

    party_id: Mapped[int] = mapped_column(ForeignKey("party_parties.id"))
    currency_id: Mapped[int] = mapped_column(ForeignKey("core_currencies.id"), nullable=True)
    pricelist_id: Mapped[Optional[int]] = mapped_column(ForeignKey("config_price_types.id"), nullable=True)
    doc_type: Mapped[str] = mapped_column(String(20), default="Invoice", info={"choices": ["Order", "Invoice"]})
    location_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stock_locations.id"), nullable=True)
    
    # Financial fields
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    total_charge: Mapped[float] = mapped_column(Float, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    
    # References
    journal_entry_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("accounting_entries.id"), nullable=True, 
        info={"ui_type": "lookup", "target_resource": "accounting/entries", "display_column": "number", "read_only": True}
    )
    stock_movement_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("stock_movements.id"), nullable=True, 
        info={"ui_type": "lookup", "target_resource": "stock/movements", "display_column": "number", "read_only": True}
    )
    pos_session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("pot_sessions.id"), nullable=True, info={"hidden": True}
    )

    # Abstract methods to be implemented by InflowInvoice / OutflowInvoice
    def get_gl_side(self) -> str:
        """Returns 'debit' or 'credit' for the primary line entries."""
        raise NotImplementedError

    def get_payment_type(self) -> str:
        """Returns 'receivable' or 'payable'."""
        raise NotImplementedError

    def get_stock_movement_type(self) -> str:
        """Returns movement type (e.g., 'delivery' or 'receipt')."""
        raise NotImplementedError

    @property
    @Aras.computed_field
    def amount_paid(self) -> float:
        db = self.db_session
        if db is None:
            return 0.0
        from apps.accounting.models import PaymentAllocation
        rows = db.query(PaymentAllocation).filter_by(
            invoice_type=self.__class__.__name__, 
            invoice_id=self.id
        ).all()
        return sum(r.amount for r in rows)

    @property
    @Aras.computed_field
    def amount_due(self) -> float:
        return self.total_amount - self.amount_paid

    @Aras.model_action(name="post", permission="edit", label="Post Invoice")
    def post(self, db):
        if self.status != "Draft":
            raise ValidationException(f"Invoice is already {self.status}.")
        
        from core.logic.handler_registry import HandlerRegistry
        from core.lib.lifecycle import Effect, dispatch
        # Both effects are optional: a free plan (POS without stock/accounting)
        # posts the document with no movement and no journal. Graceful skip,
        # not a crash. An app needing strict posting registers the consumer.
        outcome = dispatch(
            [Effect("post_stock_movement"), Effect("post_journal_entry")],
            HandlerRegistry.resolve,
            context=self,
            db=db,
        )

        self.status = "Posted"
        skipped = [n for n, r in outcome.items() if r == "skipped"]
        msg = f"{self.__class__.__name__} posted successfully."
        if skipped:
            msg += f" (skipped: {', '.join(skipped)} — provider app not installed)"
        return ok({"status": self.status, "effects": outcome}, message=msg)

    @Aras.computed_field
    def payment_allocations(self) -> list:
        db = self.db_session
        if db is None:
            return []
        from apps.accounting.models import PaymentAllocation
        return db.query(PaymentAllocation).filter_by(
            invoice_type=self.__class__.__name__, 
            invoice_id=self.id
        ).all()

    @Aras.on_delete
    def _cascade_payments(self, db):
        from apps.accounting.models import PaymentAllocation, Payment
        allocs = db.query(PaymentAllocation).filter(
            PaymentAllocation.invoice_type == self.__class__.__name__,
            PaymentAllocation.invoice_id == self.id
        ).all()
        payment_ids = {a.payment_id for a in allocs}
        for a in allocs:
            db.delete(a)
        if payment_ids:
            db.flush()
            for pid in payment_ids:
                if db.query(PaymentAllocation).filter_by(payment_id=pid).count() == 0:
                    p = db.get(Payment, pid)
                    if p and not getattr(p, "deleted_at", None):
                        p.delete_self(db)

    @property
    def journal_entries(self) -> list:
        db = self.db_session
        if db is None: return []
        from apps.accounting.models import JournalEntry
        return db.query(JournalEntry).filter_by(
            source_type=self.__class__.__name__, 
            source_id=self.id
        ).all()
