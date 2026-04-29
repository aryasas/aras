"""core.sequence — thread-safe document numbering via SELECT FOR UPDATE."""
from datetime import date
from arasCore.lib.core.extensions import db
from aras.erp.erp_core.models.sequence import Sequence


def next_number(code: str, company_id: int) -> str:
    """
    Atomically increment and return the next formatted document number.
    Uses SELECT FOR UPDATE to prevent duplicates under concurrency.
    """
    seq = (
        Sequence.query
        .filter_by(code=code, company_id=company_id)
        .with_for_update()
        .first()
    )
    if not seq:
        raise ValueError(f"Sequence '{code}' not found for company {company_id}")

    today = date.today()
    period_yearly  = str(today.year)
    period_monthly = today.strftime("%Y-%m")

    current_period = period_monthly if seq.reset_period == "monthly" else period_yearly

    if seq.reset_period != "never" and seq.last_period != current_period:
        seq.next_value = 1
        seq.last_period = current_period

    num = seq.next_value
    seq.next_value += 1
    db.session.flush()

    padded = str(num).zfill(seq.padding or 5)
    fmt = seq.format or "{prefix}/{YYYY}/{MM}/{seq}"
    result = (
        fmt
        .replace("{prefix}", seq.prefix or "")
        .replace("{suffix}", seq.suffix or "")
        .replace("{YYYY}", str(today.year))
        .replace("{MM}", today.strftime("%m"))
        .replace("{seq}", padded)
    )
    return result.strip("/")


def next_number_for_seq(seq: "Sequence") -> str:
    """Atomically increment using a pre-loaded (locked) Sequence instance."""
    today = date.today()
    current_period = today.strftime("%Y-%m") if seq.reset_period == "monthly" else str(today.year)

    if seq.reset_period != "never" and seq.last_period != current_period:
        seq.next_value = 1
        seq.last_period = current_period

    num = seq.next_value
    seq.next_value += 1
    db.session.flush()

    padded = str(num).zfill(seq.padding or 5)
    fmt = seq.format or "{prefix}/{YYYY}/{MM}/{seq}"
    return (
        fmt
        .replace("{prefix}", seq.prefix or "")
        .replace("{suffix}", seq.suffix or "")
        .replace("{YYYY}", str(today.year))
        .replace("{MM}", today.strftime("%m"))
        .replace("{seq}", padded)
    ).strip("/")
