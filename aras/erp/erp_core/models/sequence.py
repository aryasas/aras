from arasCore.lib.core.base_model import ArasModel, db


class Sequence(ArasModel):
    __tablename__ = "sequence"
    __table_args__ = (
        db.UniqueConstraint("company_id", "code", name="uq_sequence"),
    )

    company_id   = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    code         = db.Column(db.String(50), nullable=False)
    prefix       = db.Column(db.String(20), nullable=True)
    suffix       = db.Column(db.String(20), default="")
    padding      = db.Column(db.SmallInteger, default=5)
    reset_period = db.Column(db.String(10), default="yearly")  # never/yearly/monthly
    last_period  = db.Column(db.String(7), nullable=True)
    next_value   = db.Column(db.BigInteger, default=1)
    format       = db.Column(db.String(100), default="{prefix}/{YYYY}/{MM}/{seq}")

    def __repr__(self):
        return f"<Sequence {self.code}>"
