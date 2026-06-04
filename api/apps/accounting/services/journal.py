from sqlalchemy.orm import Session
from core import Aras
from core.exceptions import ValidationException
from ..models import JournalEntry, JournalEntryLine
from .org_defaults import acc_default

_BALANCE_EPSILON = 0.000001
_ROUNDING_LIMIT = 0.01


# claude-opus-4-8
def balance_journal_lines(db: Session, org_id: int, lines: list[dict]) -> list[dict]:
    total_debit = sum(float(line.get("debit", 0) or 0) for line in lines)
    total_credit = sum(float(line.get("credit", 0) or 0) for line in lines)
    diff = total_debit - total_credit

    if abs(diff) <= _BALANCE_EPSILON:
        return lines

    round_off_id = acc_default(db, org_id, "acc_round_off_id")
    if round_off_id and abs(diff) < _ROUNDING_LIMIT:
        lines.append(
            {
                "account_id": round_off_id,
                "debit": abs(diff) if diff < 0 else 0,
                "credit": abs(diff) if diff > 0 else 0,
                "description": "Rounding adjustment",
            }
        )
        total_debit = sum(float(line.get("debit", 0) or 0) for line in lines)
        total_credit = sum(float(line.get("credit", 0) or 0) for line in lines)
        diff = total_debit - total_credit
        if abs(diff) <= _BALANCE_EPSILON:
            return lines

    raise ValidationException(
        f"Journal entry is not balanced. Debit: {total_debit:.6f}, Credit: {total_credit:.6f}"
    )

class JournalService(Aras.Service):
    """Service for creating and posting journal entries."""
    model_class = JournalEntry
    
    @classmethod
    def post_entry(cls, db: Session, org_id: int, lines: list[dict], reference: str = "", narrative: str = "", currency_id: int = None, source_type: str = None, source_id: int = None) -> JournalEntry:
        """
        Create and post a balanced journal entry.
        lines: [{'account_id': int, 'debit': float, 'credit': float, 'description': str}]
        """
        lines = balance_journal_lines(db, org_id, list(lines))

        if not currency_id:
            from core.workspace.models import Organization
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
