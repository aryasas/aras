from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from ...config.models import ExchangeRate


class FxService:
    @staticmethod
    def get_rate(db: Session, currency_id: int, rate_date: Optional[date] = None) -> float:
        d = rate_date or date.today()
        row = (
            db.query(ExchangeRate)
            .filter(ExchangeRate.currency_id == currency_id, ExchangeRate.rate_date <= d)
            .order_by(ExchangeRate.rate_date.desc())
            .first()
        )
        return row.rate if row else 1.0

    @staticmethod
    def convert(
        db: Session,
        amount: float,
        from_currency_id: int,
        to_currency_id: int,
        rate_date: Optional[date] = None,
    ) -> float:
        if from_currency_id == to_currency_id:
            return amount
        from_rate = FxService.get_rate(db, from_currency_id, rate_date)
        to_rate = FxService.get_rate(db, to_currency_id, rate_date)
        if to_rate == 0:
            return amount
        return amount * (from_rate / to_rate)
