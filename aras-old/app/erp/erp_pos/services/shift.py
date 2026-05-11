"""shift_service — opening/closing shift journal entries and shift report data."""
from decimal import Decimal
from datetime import date
from arasCore.lib.core.extensions import db
from app.erp.erp_pos.models.terminal import PosSession, PosShiftEntry


def record_shift_entry(session_id: int, entry_type: str, amount: Decimal,
                       note: str = "", user_id: int = None) -> PosShiftEntry:
    """Create a PosShiftEntry and optionally post a journal entry."""
    session    = PosSession.get_or_404(session_id)
    terminal   = session.terminal
    company_id = terminal.company_id if terminal else None

    entry = PosShiftEntry.create({
        "session_id": session_id, "entry_type": entry_type,
        "amount": amount, "note": note, "entered_by_id": user_id,
    })

    if entry_type in ("opening", "cash_in", "cash_out") and company_id and float(amount) != 0:
        try:
            je = _post_shift_journal(entry, session, company_id, entry_type, amount)
            entry.set_field("journal_entry_id", je.id)
        except Exception:
            pass  # journal posting is best-effort; don't break shift operations

    return entry


def _post_shift_journal(entry: PosShiftEntry, session: PosSession,
                        company_id: int, entry_type: str, amount: Decimal):
    from app.erp.erp_acc.services.posting import post_journal, get_default_account

    cash_id     = get_default_account(company_id, "cash_default")
    suspense_id = get_default_account(company_id, "write_off")
    amt         = float(amount)
    sn          = session.shift_number or ""

    if entry_type == "opening":
        lines = [
            {"account_id": cash_id,    "debit": amt, "credit": 0,   "description": f"Opening float {sn}"},
            {"account_id": suspense_id,"debit": 0,   "credit": amt, "description": "Owner equity / petty cash fund"},
        ]
    elif entry_type == "cash_in":
        lines = [
            {"account_id": cash_id,    "debit": amt, "credit": 0,   "description": f"Cash in — {entry.note or ''}"},
            {"account_id": suspense_id,"debit": 0,   "credit": amt, "description": f"Cash in {sn}"},
        ]
    else:
        lines = [
            {"account_id": suspense_id,"debit": amt, "credit": 0,   "description": f"Cash out {sn}"},
            {"account_id": cash_id,    "debit": 0,   "credit": amt, "description": f"Cash out — {entry.note or ''}"},
        ]

    return post_journal(
        company_id=company_id, date=date.today(), lines=lines,
        reference=session.shift_number or f"SHIFT-{session.id}",
        narrative=f"POS shift {entry_type} — {session.terminal.name if session.terminal else ''}",
        origin=("pos_shift_entry", entry.id),
    )


def get_shift_report(session_id: int) -> dict:
    from app.erp.erp_acc.models.invoice import AccSalesInvoice, AccPurchaseInvoice

    session   = PosSession.get_or_404(session_id)
    sales_inv = AccSalesInvoice.find_all(pos_session_id=session_id)
    pur_inv   = AccPurchaseInvoice.find_all(pos_session_id=session_id)

    total_sales    = sum(float(i.total)      for i in sales_inv)
    total_purchase = sum(float(i.total)      for i in pur_inv)
    total_tax      = sum(float(i.charge_amt) for i in sales_inv + pur_inv)
    total_discount = sum(float(i.discount_amt) for i in sales_inv + pur_inv)

    payment_summary: dict = {}
    for inv in sales_inv + pur_inv:
        for alloc in inv.allocations:
            if alloc.payment:
                m = alloc.payment.method or "cash"
                payment_summary[m] = payment_summary.get(m, 0) + float(alloc.amount)

    entries       = list(session.entries)
    opening_float = sum(float(e.amount) for e in entries if e.entry_type == "opening")
    cash_in       = sum(float(e.amount) for e in entries if e.entry_type == "cash_in")
    cash_out      = sum(float(e.amount) for e in entries if e.entry_type == "cash_out")
    cash_sales    = payment_summary.get("cash", 0)

    return {
        "session": session, "terminal": session.terminal,
        "sales_invoices": sales_inv, "purchase_invoices": pur_inv,
        "invoice_count": len(sales_inv) + len(pur_inv),
        "total_sales": total_sales, "total_purchase": total_purchase,
        "total_tax": total_tax, "total_discount": total_discount,
        "payment_summary": payment_summary,
        "opening_float": opening_float, "cash_in": cash_in, "cash_out": cash_out,
        "cash_sales": cash_sales, "expected_cash": opening_float + cash_in + cash_sales - cash_out,
        "cash_counted": float(session.cash_counted or 0),
        "cash_difference": float(session.cash_difference or 0),
    }
