from arasCore.lib.base_model import ArasModel, db


class Currency(ArasModel):
    __tablename__ = "currency"

    code           = db.Column(db.String(3), unique=True, nullable=False)  # ISO 4217
    name           = db.Column(db.String(100), nullable=False)
    symbol         = db.Column(db.String(10), nullable=True)
    decimal_places = db.Column(db.SmallInteger, default=2)

    def __repr__(self):
        return f"<Currency {self.code}>"


class FxRate(ArasModel):
    __tablename__ = "fx_rate"
    __table_args__ = (
        db.UniqueConstraint("company_id", "from_currency_id", "to_currency_id", "valid_from",
                            name="uq_fx_rate"),
    )

    company_id       = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    from_currency_id = db.Column(db.Integer, db.ForeignKey("currency.id"), nullable=False)
    to_currency_id   = db.Column(db.Integer, db.ForeignKey("currency.id"), nullable=False)
    rate             = db.Column(db.Numeric(18, 6), nullable=False)
    valid_from       = db.Column(db.Date, nullable=False)
    source           = db.Column(db.String(10), default="manual")  # manual/bi/xe/oer

    from_currency = db.relationship("Currency", foreign_keys=[from_currency_id])
    to_currency   = db.relationship("Currency", foreign_keys=[to_currency_id])

    def __repr__(self):
        return f"<FxRate {self.from_currency_id}->{self.to_currency_id} {self.valid_from}>"
