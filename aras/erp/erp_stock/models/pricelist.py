from arasCore.lib.core.base_model import ArasModel, db


class StockPriceList(ArasModel):
    """Price list header — e.g. Retail, Wholesale, Export."""
    __tablename__ = "stock_price_list"
    __table_args__ = (
        db.UniqueConstraint("company_id", "name", name="uq_price_list_company_name"),
    )

    company_id  = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    name        = db.Column(db.String(100), nullable=False)
    currency_id = db.Column(db.Integer, db.ForeignKey("currency.id"), nullable=False)
    price_type  = db.Column(db.Enum("sales", "purchase"), nullable=False, default="sales")
    valid_from  = db.Column(db.Date, nullable=True)
    valid_to    = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text)

    currency = db.relationship("Currency")
    items    = db.relationship("StockProductPrice",
                               foreign_keys="StockProductPrice.price_list_id",
                               back_populates="price_list",
                               cascade="all, delete-orphan")
