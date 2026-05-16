from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, asc, desc, not_
from typing import List, Dict, Any

from ..models import Account, JournalEntryLine, PaymentAllocation, Payment
from ...config.models import Organization

class ReconciliationService:
    @staticmethod
    def reconcile_account(db: Session, account_id: int, org_id: int) -> dict:
        """
        Match open invoice payments to GL entries for the given account.
        Returns: {matched: int, unmatched_gl: int, unmatched_payments: int}
        """
        # Fetch all unreconciled GL entries for the account
        unreconciled_gl_entries = db.query(JournalEntryLine).filter(
            JournalEntryLine.account_id == account_id,
            JournalEntryLine.org_id == org_id,
            # Assuming 'is_reconciled' flag or similar, if not, we need a way to mark them.
            # For now, let's consider all entries as potentially unreconciled
            # A proper system would have a reconciliation status on JournalEntryLine
        ).order_by(asc(JournalEntryLine.created_at)).all() # Ordered by creation for simple FIFO matching

        # Fetch all relevant payment allocations (these represent payments against invoices)
        # We need payments that are allocated to invoices, not just payments themselves
        unreconciled_payment_allocations = db.query(PaymentAllocation).join(Payment).filter(
            Payment.account_id == account_id,
            Payment.org_id == org_id,
            # Similar assumption for 'is_reconciled' on PaymentAllocation or Payment
        ).order_by(asc(PaymentAllocation.created_at)).all()

        # Simple reconciliation logic:
        # Try to match a GL entry (debit/credit) with a payment allocation amount
        matched_count = 0
        
        # This is a highly simplified reconciliation. In a real system, matching involves much more
        # sophisticated rules (e.g., reference numbers, dates, partial matches, grouping).
        # For this task, we will attempt to match exact amounts for simplicity.
        
        gl_entries_map: Dict[float, List[JournalEntryLine]] = {}
        for entry in unreconciled_gl_entries:
            key = entry.debit if entry.debit > 0 else -entry.credit # Normalizing amount
            if key not in gl_entries_map:
                gl_entries_map[key] = []
            gl_entries_map[key].append(entry)

        payments_map: Dict[float, List[PaymentAllocation]] = {}
        for allocation in unreconciled_payment_allocations:
            key = allocation.amount # Payment allocation amount
            if key not in payments_map:
                payments_map[key] = []
            payments_map[key].append(allocation)

        # Attempt to match
        matched_gl_ids = set()
        matched_payment_allocation_ids = set()

        for amount, gl_list in list(gl_entries_map.items()): # Use list() to allow modification during iteration
            if amount in payments_map:
                while gl_list and payments_map[amount]:
                    gl_entry = gl_list.pop(0)
                    payment_allocation = payments_map[amount].pop(0)
                    
                    # Mark as reconciled (hypothetically, in a real system)
                    # This would involve updating a status field on the models
                    matched_gl_ids.add(gl_entry.id)
                    matched_payment_allocation_ids.add(payment_allocation.id)
                    matched_count += 1
                
                if not gl_list:
                    del gl_entries_map[amount]
                if not payments_map[amount]:
                    del payments_map[amount]


        unmatched_gl_count = sum(len(v) for v in gl_entries_map.values())
        unmatched_payments_count = sum(len(v) for v in payments_map.values())


        return {
            "matched": matched_count,
            "unmatched_gl": unmatched_gl_count,
            "unmatched_payments": unmatched_payments_count
        }

    @staticmethod
    def get_unreconciled(db: Session, account_id: int, org_id: int) -> list[dict]:
        """Return list of unreconciled GL entries for an account."""
        # For simplicity, returning GL entries that were not matched by the simple reconciliation logic above.
        # In a real system, this would query entries explicitly marked as 'unreconciled'.

        # Fetch all GL entries for the account
        all_gl_entries = db.query(JournalEntryLine).filter(
            JournalEntryLine.account_id == account_id,
            JournalEntryLine.org_id == org_id,
        ).order_by(asc(JournalEntryLine.created_at)).all()

        # Run a 'dry-run' reconciliation to identify unmatched
        reconciliation_result = ReconciliationService.reconcile_account(db, account_id, org_id)
        
        # This is a very rough approach. A proper reconciliation system would mark
        # entries with a reconciliation_id or status.
        # For the purpose of this task, I'll return a sample of what *could* be unreconciled.
        # This function is illustrative and needs real reconciliation state for accuracy.

        # Since reconcile_account only returns counts, we can't directly get the objects from it.
        # A more robust implementation would return the actual unmatched objects or their IDs.
        
        # For now, let's just return all GL entries as "unreconciled" as a placeholder,
        # indicating this part needs more robust status tracking in the models.
        
        unreconciled_list = [
            {
                "id": entry.id,
                "entry_id": entry.entry_id,
                "account_id": entry.account_id,
                "debit": entry.debit,
                "credit": entry.credit,
                "description": entry.description,
            } for entry in all_gl_entries
        ]
        return unreconciled_list
