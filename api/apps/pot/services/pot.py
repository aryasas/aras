# claude-sonnet-4-6
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import date
from core import Aras
from core.response import ok, err
from core.exceptions import ValidationException
from ..models import PotSession
from apps.stock.models import Item
from apps.accounting.models import InflowInvoice, OutflowInvoice, InflowInvoiceLine, OutflowInvoiceLine, Payment, PaymentAllocation

class PotService(Aras.Service):
    """
    Business logic for Point of Sale (POT) operations.
    """

    @staticmethod
    def open_session(db: Session, terminal_id: int, opening_balance: float, user_id: int, org_id: int) -> PotSession:
        session = PotSession(
            org_id=org_id,
            terminal_id=terminal_id,
            opening_balance=opening_balance,
            status="Draft",
            doc_date=date.today()
        )
        session.save(db, user_id=user_id)
        db.commit()
        return session

    @staticmethod
    def close_session(db: Session, session_id: int, closing_balance: float, user_id: int) -> PotSession:
        session = db.get(PotSession, session_id)
        if not session:
            raise ValidationException("Session not found")
        session.closing_balance = closing_balance
        session.status = "Posted"
        db.commit()
        return session

    @staticmethod
    def process_quick_invoice(db: Session, session: PotSession, items_data: List[Dict], party_id: Optional[int], payment_mode_id: Optional[int], amount_paid: float, user_id: int, mode: str = None) -> Dict[str, Any]:
        from ..routers import _org_base_currency_id, _payment_account_id
        
        org_id = session.org_id
        currency_id = _org_base_currency_id(db, org_id)
        
        effective_mode = mode or session.mode or "sales"
        if effective_mode == "sales":
            invoice_cls = InflowInvoice
            line_cls = InflowInvoiceLine
        else:
            invoice_cls = OutflowInvoice
            line_cls = OutflowInvoiceLine
            
        # Create Invoice
        invoice = invoice_cls(
            org_id=org_id,
            party_id=party_id,
            currency_id=currency_id,
            pos_session_id=session.id,
            status="Draft",
            doc_date=date.today()
        )
        invoice.save(db, user_id=user_id)
        
        total_amount = 0
        for it in items_data:
            item_id = it["item_id"]
            qty = it["qty"]
            price = it["unit_price"]
            line = line_cls(
                invoice_id=invoice.id,
                item_id=item_id,
                qty=qty,
                unit_price=price,
            )
            db.add(line)
            total_amount += qty * price
            
        db.flush()
        
        from core.logic.handler_registry import HandlerRegistry

        # Stock movement always runs first
        fn = HandlerRegistry.resolve("post_stock_movement")
        if fn:
            fn(db=db, item=invoice, params={})

        # Create Payment first when paid
        payment = None
        if amount_paid > 0:
            if not currency_id:
                raise ValidationException("Organization base currency is required before creating POS payments")

            account_id = _payment_account_id(db, org_id, payment_mode_id)
            if not account_id:
                raise ValidationException("Cash/Bank account is required before creating POS payments")

            payment = Payment(
                org_id=org_id,
                currency_id=currency_id,
                payment_type="Incoming" if effective_mode == "sales" else "Outgoing",
                party_type="Customer" if effective_mode == "sales" else "Supplier",
                party_id=party_id,
                account_id=account_id,
                mode_of_payment_id=payment_mode_id,
                amount=amount_paid,
                status="Posted",
                doc_date=date.today()
            )
            payment.save(db, user_id=user_id)

        # Journal entry
        fn = HandlerRegistry.resolve("post_journal_entry")
        if fn:
            journal_params = {}
            if payment is not None:
                journal_params["payment_account_id"] = payment.account_id
                journal_params["payment"] = payment
                journal_params["amount_paid"] = amount_paid
            fn(db=db, item=invoice, params=journal_params)

        invoice.status = "Posted"
        db.flush()

        if payment is not None:
            alloc = PaymentAllocation(
                payment_id=payment.id,
                invoice_type=invoice_cls.__name__,
                invoice_id=invoice.id,
                amount=min(amount_paid, total_amount),
            )
            db.add(alloc)
            
        db.flush()
        db.commit()
        db.refresh(invoice)
        
        return {
            "invoice_number": invoice.number,
            "invoice_id": invoice.id,
            "change_amount": max(0, amount_paid - total_amount) if effective_mode == "sales" else 0
        }
