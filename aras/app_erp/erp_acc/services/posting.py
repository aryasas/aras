"""acc.posting — the ONLY way to create posted journal entries."""
from decimal import Decimal
from datetime import date as date_type, datetime
from flask_login import current_user
from arasCore.lib.extensions import db
from aras.app_erp.erp_acc.models.journal import AccJournalEntry, AccJournalLine
from aras.app_erp.erp_core.models.fiscal import FiscalPeriod
from aras.app_erp.erp_core.services import sequence as seq_svc
from aras.app_erp.erp_core.services import audit as audit_svc


def post_journal(
    company_id: int,
    date: date_type,
    lines: list,
    reference: str = "",
    narrative: str = "",
    origin: tuple = None,
    sequence_code: str = "accounting.journal",
    journal_code: str = None,  # kept for backwards compat, unused
) -> AccJournalEntry:
    """
    Atomically create and post a balanced journal entry.
    lines: list of dicts with keys: account_id, debit, credit,
           and optionally: partner_type, partner_id, currency_id,
           amount_currency, fx_rate, tax_id, tax_base_amount,
           analytic_tag_id, description
    """
    period = _resolve_period(company_id, date)
    if period and period.state == "closed":
        raise ValueError(f"Fiscal period '{period.code}' is closed")

    total_debit  = sum(Decimal(str(l.get("debit",  0))) for l in lines)
    total_credit = sum(Decimal(str(l.get("credit", 0))) for l in lines)
    if abs(total_debit - total_credit) > Decimal("0.01"):
        raise ValueError(f"Journal not balanced: debit={total_debit} credit={total_credit}")

    entry_name = seq_svc.next_number(sequence_code, company_id)

    user_id = None
    try:
        if current_user and current_user.is_authenticated:
            user_id = current_user.id
    except RuntimeError:
        pass

    entry = AccJournalEntry(
        company_id=company_id,
        name=entry_name,
        date_entry=date,
        reference=reference,
        narrative=narrative,
        state="posted",
        fiscal_period_id=period.id if period else None,
        amount_total=total_debit,
        posted_at=datetime.utcnow(),
        posted_by=user_id,
    )
    if origin:
        entry.origin_model, entry.origin_id = origin

    db.session.add(entry)
    db.session.flush()

    for i, l in enumerate(lines):
        db.session.add(AccJournalLine(
            entry_id=entry.id,
            sequence=i,
            account_id=l["account_id"],
            partner_type=l.get("partner_type", "none"),
            partner_id=l.get("partner_id"),
            debit=Decimal(str(l.get("debit", 0))),
            credit=Decimal(str(l.get("credit", 0))),
            currency_id=l.get("currency_id"),
            amount_currency=l.get("amount_currency"),
            fx_rate=l.get("fx_rate"),
            tax_id=l.get("tax_id"),
            tax_base_amount=l.get("tax_base_amount"),
            analytic_tag_id=l.get("analytic_tag_id"),
            description=l.get("description", ""),
        ))

    audit_svc.log("acc_journal_entry", entry.id, "post", company_id=company_id)
    return entry


def reverse_entry(entry_id: int, date: date_type, narrative: str = "") -> AccJournalEntry:
    """Create a mirror entry with debit/credit swapped."""
    orig = AccJournalEntry.get(entry_id)
    if not orig or orig.state != "posted":
        raise ValueError("Can only reverse a posted entry")

    rev_lines = [
        {
            "account_id":      l.account_id,
            "debit":           l.credit,
            "credit":          l.debit,
            "partner_type":    l.partner_type,
            "partner_id":      l.partner_id,
            "currency_id":     l.currency_id,
            "amount_currency": (-l.amount_currency) if l.amount_currency else None,
            "fx_rate":         l.fx_rate,
            "tax_id":          l.tax_id,
            "tax_base_amount": l.tax_base_amount,
            "analytic_tag_id": l.analytic_tag_id,
            "description":     f"REV: {l.description or ''}",
        }
        for l in orig.lines
    ]

    return post_journal(
        company_id=orig.company_id,
        date=date,
        lines=rev_lines,
        reference=f"REV:{orig.name}",
        narrative=narrative or f"Reversal of {orig.name}",
        origin=("acc_journal_entry", orig.id),
    )


def get_default_account(company_id: int, key: str) -> int:
    """Resolve a default account ID from Company fields (e.g. key='cash_default' → acc_cash_default_id)."""
    from aras.app_erp.erp_core.models.company import Company
    company = Company.get(company_id)
    if not company:
        raise ValueError(f"Company {company_id} not found")
    field = f"acc_{key}_id"
    acc_id = getattr(company, field, None)
    if not acc_id:
        raise ValueError(f"Default account '{key}' not configured for company {company_id}")
    return acc_id


def _resolve_period(company_id: int, d: date_type):
    from aras.app_erp.erp_core.models.fiscal import FiscalYear
    return (
        FiscalPeriod.query
        .join(FiscalYear, FiscalYear.id == FiscalPeriod.fiscal_year_id)
        .filter(
            FiscalYear.company_id == company_id,
            FiscalPeriod.date_start <= d,
            FiscalPeriod.date_end >= d,
        )
        .first()
    )
