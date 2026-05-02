from arasCore.lib.core.base_model import ArasModel, db


class StockPriceType(ArasModel):
    """Named price group/reference — e.g. Retail, Wholesale, Promo A."""
    __tablename__ = "stock_price_type"
    __table_args__ = (
        db.UniqueConstraint("company_id", "name", name="uq_price_type_company_name"),
    )

    company_id  = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    name        = db.Column(db.String(100), nullable=False)
    currency_id = db.Column(db.Integer, db.ForeignKey("currency.id"), nullable=False)
    description = db.Column(db.Text)

    currency = db.relationship("Currency")
    items    = db.relationship("StockPriceList",
                               foreign_keys="StockPriceList.price_type_id",
                               back_populates="price_type",
                               cascade="all, delete-orphan")
