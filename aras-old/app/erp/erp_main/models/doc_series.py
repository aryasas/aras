# -*- coding: utf-8 -*-
"""DocSeries — unified document numbering / naming series.

Replaces the former Sequence + NamingSeries pair. Per (company_id, code).

Two consumers:
  * Service callers: ``next_code(company_id, code)`` → formatted string
  * Auto-naming hook on ArasModel: a model sets ``__naming_series__ = "<code>"``
    and DocSeries row's ``format`` defines the pattern.

Pattern tokens supported in ``format`` (and legacy ``pattern``):
    {prefix} / {suffix}    static text from the row
    {YYYY} / {YY}          year
    {MM} / {DD}            month / day
    {seq} / {####}         counter (seq = padded by `padding`; #### = N hashes)
    {COMPANY}              company code (resolved from row's company)
"""
import re
from datetime import date, datetime
from arasCore.arasgen import ArasGen
from arasCore.lib.core.base_model import db
from app.erp.erp_main.manifest import Main


class DocSeries(ArasGen.Model, module=Main):
    __tablename__ = "main_doc_series"
    __title__     = "Doc Series"
    __icon__      = "fa-sort-numeric-asc"
    __menu_order__= 0
    __searchable__ = ("code", "format")
    __table_args__ = (
        db.UniqueConstraint("company_id", "code", name="uq_doc_series"),
    )

    company_id   = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=True)
    code         = db.Column(db.String(80),  nullable=False, index=True)
    description  = db.Column(db.String(200), nullable=True)
    prefix       = db.Column(db.String(20),  nullable=True)
    suffix       = db.Column(db.String(20),  default="")
    padding      = db.Column(db.SmallInteger, default=5)
    reset_period = db.Column(db.String(10), default="yearly")  # never/yearly/monthly
    last_period  = db.Column(db.String(7),  nullable=True)
    next_value   = db.Column(db.BigInteger, default=1)
    format       = db.Column(db.String(120), default="{prefix}/{YYYY}/{MM}/{seq}")
    is_active    = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<DocSeries {self.code}>"


# ── Formatting ────────────────────────────────────────────────────────────────

def _expand_format(seq: DocSeries, num: int) -> str:
    today = date.today()
    padded = str(num).zfill(seq.padding or 5)
    fmt = seq.format or "{prefix}/{YYYY}/{MM}/{seq}"
    out = (fmt
        .replace("{prefix}",  seq.prefix or "")
        .replace("{suffix}",  seq.suffix or "")
        .replace("{YYYY}",    f"{today.year:04d}")
        .replace("{YY}",      f"{today.year % 100:02d}")
        .replace("{MM}",      f"{today.month:02d}")
        .replace("{DD}",      f"{today.day:02d}")
        .replace("{seq}",     padded)
    )
    # {####} → counter zero-padded to N hashes
    out = re.sub(r"\{(#+)\}", lambda m: f"{num:0{len(m.group(1))}d}", out)
    # {COMPANY} → company code if available
    company_code = ""
    if seq.company_id:
        try:
            from app.erp.erp_config.models.company import Company
            c = Company.get(seq.company_id)
            company_code = (c.code if c else "") or ""
        except Exception:
            pass
    out = out.replace("{COMPANY}", company_code)
    return out.strip("/")


def _advance(seq: DocSeries) -> int:
    today = date.today()
    period = today.strftime("%Y-%m") if seq.reset_period == "monthly" else str(today.year)
    if seq.reset_period and seq.reset_period != "never" and seq.last_period != period:
        seq.next_value = 1
        seq.last_period = period
    num = seq.next_value or 1
    seq.next_value = num + 1
    db.session.flush()
    return num
