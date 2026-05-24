from sqlalchemy.orm import Session
from sqlalchemy import func

from apps.accounting.models import JournalEntry, JournalEntryLine, Payment, PaymentAllocation

class ReconciliationService:
    @staticmethod
    def reconcile_account(db: Session, account_id: int, org_id: int) -> dict:
        """
        Match open invoice payments to GL entries for the given account.
        Returns: {matched: int, unmatched_gl: int, unmatched_payments: int}
        """
        # This is a simplified reconciliation. In a real ERP, this would be much more complex,
        # involving matching rules, aging, and user intervention.
        # Here, we'll try to match GL entries for invoices with payment allocations.

        unmatched_gl_entries = db.query(JournalEntryLine).filter(
            JournalEntryLine.account_id == account_id,
            JournalEntryLine.parent.has(JournalEntry.org_id == org_id),
            JournalEntryLine.parent.has(JournalEntry.status == "Posted") # Only posted entries
        ).all()

        unmatched_payments = db.query(PaymentAllocation).filter(
            PaymentAllocation.parent.has(Payment.org_id == org_id),
            PaymentAllocation.parent.has(Payment.status == "Posted"),
            PaymentAllocation.parent.has(Payment.account_id == account_id),
            # Add logic to determine if allocation is "open" / not fully reconciled
            # For simplicity, we assume all allocations are pending reconciliation if not linked to a specific JE
        ).all()

        matched_count = 0
        unmatched_gl_count = len(unmatched_gl_entries)
        unmatched_payments_count = len(unmatched_payments)

        # In a real scenario, matching logic would go here.
        # For this exercise, we'll just report counts.

        return {
            "matched": matched_count,
            "unmatched_gl": unmatched_gl_count,
            "unmatched_payments": unmatched_payments_count
        }

    @staticmethod
    def get_unreconciled(db: Session, account_id: int, org_id: int) -> list[dict]:
        """Return list of unreconciled GL entries for an account."""
        # Similar to reconcile_account, this would involve complex queries to find truly unreconciled items.
        # For simplicity, we'll return a subset of the unmatched GL entries.
        unmatched_gl_entries = db.query(JournalEntryLine).filter(
            JournalEntryLine.account_id == account_id,
            JournalEntryLine.parent.has(JournalEntry.org_id == org_id),
            JournalEntryLine.parent.has(JournalEntry.status == "Posted")
        ).order_by(JournalEntryLine.created_at.desc()).limit(10).all() # Just return recent 10 for example

        return [{
            "journal_entry_line_id": jel.id,
            "journal_entry_number": jel.parent.number,
            "description": jel.description,
            "debit": jel.debit,
            "credit": jel.credit,
            "date": jel.parent.doc_date
        } for jel in unmatched_gl_entries]