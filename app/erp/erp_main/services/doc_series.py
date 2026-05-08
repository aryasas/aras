"""DocSeries service — atomic document numbering.

Public API:
    next_code(company_id, code, *, default_format=None) -> str
        Look up DocSeries row (company_id, code), increment, return formatted name.
        If row missing and ``default_format`` given, auto-create.
    next_for_seq(seq) -> str
        Increment a pre-loaded (locked) row.

Legacy aliases kept for now: ``next_number``, ``next_number_for_seq``.
"""
from app.erp.erp_main.models.doc_series import DocSeries, _expand_format, _advance
from arasCore.lib.core.extensions import db


def next_code(company_id: int | None, code: str, *, default_format: str | None = None) -> str:
    q = DocSeries.query.filter_by(code=code, company_id=company_id).with_for_update()
    seq = q.first()
    if seq is None and company_id is not None:
        # fall back to global (company_id NULL) row
        seq = DocSeries.query.filter_by(code=code, company_id=None).with_for_update().first()
    if seq is None:
        if not default_format:
            raise ValueError(f"DocSeries '{code}' not found for company {company_id}")
        seq = DocSeries(company_id=company_id, code=code, format=default_format,
                        next_value=1, padding=5, reset_period="yearly")
        db.session.add(seq)
        db.session.flush()
    num = _advance(seq)
    return _expand_format(seq, num)


def next_for_seq(seq: DocSeries) -> str:
    num = _advance(seq)
    return _expand_format(seq, num)


# ── Legacy aliases ────────────────────────────────────────────────────────────
next_number          = next_code
next_number_for_seq  = next_for_seq


def next_for_table(table_name: str, default_format: str = "") -> str:
    """Auto-name hook target — no company context.
    Looks up by code=table_name with company_id=NULL.
    """
    seq = DocSeries.query.filter_by(code=table_name, company_id=None, is_active=True).first()
    if seq is None:
        if not default_format:
            return ""
        seq = DocSeries(code=table_name, company_id=None, format=default_format,
                        next_value=1, padding=4, reset_period="yearly", is_active=True)
        db.session.add(seq)
        db.session.flush()
    num = _advance(seq)
    return _expand_format(seq, num)
