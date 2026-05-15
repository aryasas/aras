from typing import Optional
from sqlalchemy.orm import Session
from ..models import Payment, PaymentAllocation, SalesInvoice, PurchaseInvoice, Account, ModeOfPayment, CompanyPaymentAccount
from .journal import JournalService


class PaymentService:

    @staticmethod
    def _resolve_cash_account(db: Session, payment: Payment) -> Optional[Account]:
        """Maps payment mode → GL account via CompanyPaymentAccount."""
        if payment.mode_of_payment_id:
            mapping = db.query(CompanyPaymentAccount).filter(
                CompanyPaymentAccount.mode_id == payment.mode_of_payment_id
            ).first()
            if mapping:
                return db.query(Account).get(mapping.account_id)
        # Fallback: any asset account
        return db.query(Account).filter(
            Account.company_id == payment.company_id,
            Account.account_type == "Asset",
            Account.is_group == False
        ).first()

    @staticmethod
    def post_payment(db: Session, payment: Payment):
        """Post payment to GL: debit cash, credit AR (incoming) or debit AP, credit cash (outgoing)."""
        if payment.status != "Draft":
            return {"error": f"Payment is already {payment.status}"}

        cash_account = PaymentService._resolve_cash_account(db, payment)
        if not cash_account:
            return {"error": "Cash/Bank account not configured for this payment mode."}

        if payment.payment_type == "Incoming":
            ar_account = db.query(Account).filter(
                Account.company_id == payment.company_id,
                Account.account_type == "Asset",
                Account.is_group == False
            ).first()
            if not ar_account:
                return {"error": "AR account not found."}
            lines = [
                {"account_id": cash_account.id, "debit": payment.amount, "credit": 0,
                 "description": f"Payment received: {payment.number}"},
                {"account_id": ar_account.id, "debit": 0, "credit": payment.amount,
                 "description": f"Clear receivable: {payment.number}"},
            ]
        else:
            ap_account = db.query(Account).filter(
                Account.company_id == payment.company_id,
                Account.account_type == "Liability",
                Account.is_group == False
            ).first()
            if not ap_account:
                return {"error": "AP account not found."}
            lines = [
                {"account_id": ap_account.id, "debit": payment.amount, "credit": 0,
                 "description": f"Clear payable: {payment.number}"},
                {"account_id": cash_account.id, "debit": 0, "credit": payment.amount,
                 "description": f"Payment made: {payment.number}"},
            ]

        try:
            JournalService.post_entry(
                db, payment.company_id, lines,
                reference=payment.number,
                narrative=f"Auto-posted from Payment {payment.number}"
            )
            payment.status = "Posted"
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return {"error": str(e)}

    @staticmethod
    def get_unpaid_invoices(db: Session, party_type: str, party_id: int, company_id: int) -> list:
        """Returns open/partial invoices for a party ordered by date (FIFO)."""
        if party_type == "Customer":
            invoices = db.query(SalesInvoice).filter(
                SalesInvoice.company_id == company_id,
                SalesInvoice.customer_id == party_id,
                SalesInvoice.status.in_(["Posted", "Partial"])
            ).order_by(SalesInvoice.doc_date).all()
        elif party_type == "Supplier":
            invoices = db.query(PurchaseInvoice).filter(
                PurchaseInvoice.company_id == company_id,
                PurchaseInvoice.supplier_id == party_id,
                PurchaseInvoice.status.in_(["Posted", "Partial"])
            ).order_by(PurchaseInvoice.doc_date).all()
        else:
            invoices = []
        return invoices

    @staticmethod
    def auto_allocate(db: Session, payment: Payment) -> dict:
        """FIFO allocation of payment amount to unpaid invoices."""
        if payment.status != "Posted":
            return {"error": "Payment must be Posted before allocation."}

        invoices = PaymentService.get_unpaid_invoices(
            db, payment.party_type, payment.party_id, payment.company_id
        )
        invoice_type = "SalesInvoice" if payment.party_type == "Customer" else "PurchaseInvoice"

        remaining = payment.amount
        allocated_count = 0

        for inv in invoices:
            if remaining <= 0:
                break
            amount_due = inv.total_amount - sum(a.amount for a in inv.allocations)
            if amount_due <= 0:
                continue
            alloc_amount = min(remaining, amount_due)
            alloc = PaymentAllocation(
                payment_id=payment.id,
                invoice_type=invoice_type,
                invoice_id=inv.id,
                amount=alloc_amount
            )
            db.add(alloc)
            remaining -= alloc_amount
            allocated_count += 1
            # Update invoice status
            new_paid = sum(a.amount for a in inv.allocations) + alloc_amount
            if new_paid >= inv.total_amount - 0.01:
                inv.status = "Paid"
            else:
                inv.status = "Partial"

        db.commit()
        return {"allocated": allocated_count, "remaining": remaining}

    @staticmethod
    def allocate(db: Session, payment: Payment, invoice_type: str, invoice_id: int, amount: float) -> dict:
        """Manually allocate a specific amount to a specific invoice."""
        if payment.status != "Posted":
            return {"error": "Payment must be Posted before allocation."}

        if invoice_type == "SalesInvoice":
            inv = db.query(SalesInvoice).get(invoice_id)
        else:
            inv = db.query(PurchaseInvoice).get(invoice_id)

        if not inv:
            return {"error": "Invoice not found."}

        amount_due = inv.total_amount - sum(a.amount for a in inv.allocations)
        if amount > amount_due + 0.01:
            return {"error": f"Amount exceeds invoice balance of {amount_due:.2f}"}

        alloc = PaymentAllocation(
            payment_id=payment.id,
            invoice_type=invoice_type,
            invoice_id=invoice_id,
            amount=amount
        )
        db.add(alloc)

        new_paid = sum(a.amount for a in inv.allocations) + amount
        if new_paid >= inv.total_amount - 0.01:
            inv.status = "Paid"
        else:
            inv.status = "Partial"

        db.commit()
        return {"ok": True}

    @staticmethod
    def deallocate(db: Session, allocation_id: int) -> dict:
        """Remove an allocation and revert invoice status."""
        alloc = db.query(PaymentAllocation).get(allocation_id)
        if not alloc:
            return {"error": "Allocation not found."}

        if alloc.invoice_type == "SalesInvoice":
            inv = db.query(SalesInvoice).get(alloc.invoice_id)
        else:
            inv = db.query(PurchaseInvoice).get(alloc.invoice_id)

        db.delete(alloc)
        db.flush()

        if inv:
            remaining_paid = sum(a.amount for a in inv.allocations)
            if remaining_paid <= 0:
                inv.status = "Posted"
            elif remaining_paid < inv.total_amount - 0.01:
                inv.status = "Partial"

        db.commit()
        return {"ok": True}
