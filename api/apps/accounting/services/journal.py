from sqlalchemy.orm import Session
from ..models import JournalEntry, JournalEntryLine

class JournalService:
    """Service for creating and posting journal entries."""
    
    @staticmethod
    def post_entry(db: Session, org_id: int, lines: list[dict], reference: str = "", narrative: str = "", currency_id: int = None, source_type: str = None, source_id: int = None) -> JournalEntry:
        """
        Create and post a balanced journal entry.
        lines: [{'account_id': int, 'debit': float, 'credit': float, 'description': str}]
        """
        total_debit = sum(l.get('debit', 0) for l in lines)
        total_credit = sum(l.get('credit', 0) for l in lines)

        if abs(total_debit - total_credit) > 0.001:
            raise ValueError(f"Journal not balanced. Debit: {total_debit}, Credit: {total_credit}")

        if not currency_id:
            from apps.config.models import Organization
            co = db.get(Organization, org_id)
            currency_id = co.base_currency_id if co else None

        entry = JournalEntry(
            org_id=org_id,
            number=reference,
            currency_id=currency_id,
            narrative=narrative,
            source_type=source_type,
            source_id=source_id,
            status="Posted"
        )
        db.add(entry)
        db.flush()
        
        for i, l in enumerate(lines):
            line = JournalEntryLine(
                entry_id=entry.id,
                sequence=(i + 1) * 10,
                account_id=l['account_id'],
                debit=l.get('debit', 0),
                credit=l.get('credit', 0),
                description=l.get('description', '')
            )
            db.add(line)
            
        return entry
