"""core.fx — currency conversion helper."""
from decimal import Decimal
from datetime import date
from aras.erp.erp_core.models.currency import Currency, FxRate


def convert(amount: Decimal, from_code: str, to_code: str,
            on_date: date = None, company_id: int = None) -> Decimal:
    if from_code == to_code:
        return Decimal(amount)
    if on_date is None:
        on_date = date.today()

    from_cur = Currency.find(code=from_code)
    to_cur   = Currency.find(code=to_code)
    if not from_cur or not to_cur:
        raise ValueError(f"Unknown currency: {from_code} or {to_code}")

    rate_row = (
        FxRate.query
        .filter(FxRate.from_currency_id == from_cur.id,
                FxRate.to_currency_id   == to_cur.id,
                FxRate.valid_from        <= on_date)
        .order_by(FxRate.valid_from.desc())
        .first()
    )
    if not rate_row:
        raise ValueError(f"No FX rate for {from_code}->{to_code} on or before {on_date}")

    return (Decimal(amount) * rate_row.rate).quantize(Decimal("0.01"))
