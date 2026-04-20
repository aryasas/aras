"""core.fx — currency conversion helper."""
from decimal import Decimal
from datetime import date
from arasCore.lib.extensions import db
from aras.app_erp.erp_core.models.currency import CoreFxRate


def convert(amount: Decimal, from_code: str, to_code: str,
            on_date: date = None, company_id: int = None) -> Decimal:
    if from_code == to_code:
        return Decimal(amount)
    if on_date is None:
        on_date = date.today()

    from aras.app_erp.erp_core.models.currency import CoreCurrency
    from_cur = CoreCurrency.query.filter_by(code=from_code).first()
    to_cur   = CoreCurrency.query.filter_by(code=to_code).first()
    if not from_cur or not to_cur:
        raise ValueError(f"Unknown currency: {from_code} or {to_code}")

    rate_row = (
        CoreFxRate.query
        .filter(
            CoreFxRate.from_currency_id == from_cur.id,
            CoreFxRate.to_currency_id   == to_cur.id,
            CoreFxRate.valid_from        <= on_date,
        )
        .order_by(CoreFxRate.valid_from.desc())
        .first()
    )
    if not rate_row:
        raise ValueError(f"No FX rate for {from_code}->{to_code} on or before {on_date}")

    return (Decimal(amount) * rate_row.rate).quantize(Decimal("0.01"))
