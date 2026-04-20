from arasCore.lib.base_model import ArasModel, db


class StockPriceList(ArasModel):
    """Price list header — e.g. Retail, Wholesale, Export."""
    __tablename__ = "stock_price_list"
    __table_args__ = (
        db.UniqueConstraint("company_id", "name", name="uq_price_list_company_name"),
    )

    company_id  = db.Column(db.Integer, db.ForeignKey("core_company.id"), nullable=False)
    name        = db.Column(db.String(100), nullable=False)
    currency_id = db.Column(db.Integer, db.ForeignKey("core_currency.id"), nullable=False)
    price_type  = db.Column(db.Enum("sales", "purchase"), nullable=False, default="sales")
    valid_from  = db.Column(db.Date, nullable=True)
    valid_to    = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text)

    currency = db.relationship("CoreCurrency")
    items    = db.relationship("StockPriceListItem", backref="price_list", cascade="all, delete-orphan")


class StockPriceListItem(ArasModel):
    """Price per product per UOM in a price list."""
    __tablename__ = "stock_price_list_item"
    __table_args__ = (
        db.UniqueConstraint("price_list_id", "product_id", "uom_id", "min_qty",
                            name="uq_price_list_item"),
    )

    price_list_id = db.Column(db.Integer, db.ForeignKey("stock_price_list.id"), nullable=False)
    product_id    = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=False)
    uom_id        = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=False)
    price         = db.Column(db.Numeric(18, 4), nullable=False)
    min_qty       = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    discount_pct  = db.Column(db.Numeric(6, 2), default=0, nullable=False)
    valid_from    = db.Column(db.Date, nullable=True)
    valid_to      = db.Column(db.Date, nullable=True)

    uom = db.relationship("StockUom")
