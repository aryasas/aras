from arasCore.lib.core.base_model import ArasModel, db


class StockProductCategory(ArasModel):
    __tablename__ = "stock_product_category"

    name                 = db.Column(db.String(100), nullable=False)
    parent_id            = db.Column(db.Integer, db.ForeignKey("stock_product_category.id"), nullable=True)
    account_stock_id     = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    account_cogs_id      = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    account_revenue_id   = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    account_purchase_id  = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    account_variance_id  = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    valuation_method     = db.Column(db.Enum("standard", "average", "fifo"), nullable=False, default="average")

    parent           = db.relationship("StockProductCategory", remote_side="StockProductCategory.id",
                                       backref="children")
    account_stock    = db.relationship("AccAccount", foreign_keys=[account_stock_id])
    account_cogs     = db.relationship("AccAccount", foreign_keys=[account_cogs_id])
    account_revenue  = db.relationship("AccAccount", foreign_keys=[account_revenue_id])
    account_purchase = db.relationship("AccAccount", foreign_keys=[account_purchase_id])
    account_variance = db.relationship("AccAccount", foreign_keys=[account_variance_id])


class StockProduct(ArasModel):
    __tablename__ = "stock_product"
    __table_args__ = (
        db.UniqueConstraint("company_id", "code", name="uq_stock_product_company_code"),
    )

    company_id          = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    code                = db.Column(db.String(50), nullable=False)
    name                = db.Column(db.String(200), nullable=False)
    description         = db.Column(db.Text)
    category_id         = db.Column(db.Integer, db.ForeignKey("stock_product_category.id"), nullable=True)
    uom_id              = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=False)
    uom_purchase_id     = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=True)
    uom_sales_id        = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=True)
    is_stock_item       = db.Column(db.Boolean, default=True, nullable=False)
    for_sales           = db.Column(db.Boolean, default=True, nullable=False)
    for_purchase        = db.Column(db.Boolean, default=True, nullable=False)
    use_price_table     = db.Column(db.Boolean, default=False, nullable=False)
    account_revenue_id  = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    account_purchase_id = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    account_cogs_id     = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)

    category         = db.relationship("StockProductCategory")
    uom              = db.relationship("StockUom", foreign_keys=[uom_id])
    uom_purchase     = db.relationship("StockUom", foreign_keys=[uom_purchase_id])
    uom_sales        = db.relationship("StockUom", foreign_keys=[uom_sales_id])
    account_revenue  = db.relationship("AccAccount", foreign_keys=[account_revenue_id])
    account_purchase = db.relationship("AccAccount", foreign_keys=[account_purchase_id])
    account_cogs     = db.relationship("AccAccount", foreign_keys=[account_cogs_id])
    uom_alts         = db.relationship("StockProductUom", backref="product", cascade="all, delete-orphan")
    prices           = db.relationship("StockProductPrice", backref="product", cascade="all, delete-orphan")
    account_links    = db.relationship("StockProductAccountLink", backref="product", cascade="all, delete-orphan")
    bundle_components = db.relationship(
        "StockProductBundle", foreign_keys="StockProductBundle.bundle_id",
        backref="bundle", cascade="all, delete-orphan"
    )
    valuations = db.relationship("StockValuation", foreign_keys="StockValuation.product_id",
                                 cascade="all, delete-orphan")


class StockProductUom(ArasModel):
    """Alternative UOMs for a product with per-product conversion factor."""
    __tablename__ = "stock_product_uom"
    __table_args__ = (
        db.UniqueConstraint("product_id", "uom_id", name="uq_stock_product_uom"),
    )

    product_id = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=False)
    uom_id     = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=False)
    factor     = db.Column(db.Numeric(18, 6), nullable=False)
    barcode    = db.Column(db.String(100), nullable=True)
    is_active  = db.Column(db.Boolean, default=True, nullable=False)

    uom = db.relationship("StockUom")


class StockProductPrice(ArasModel):
    """Price table per product — supports both direct product prices and price-list-based prices."""
    __tablename__ = "stock_product_price"

    product_id    = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=False)
    price_list_id = db.Column(db.Integer, db.ForeignKey("stock_price_list.id"), nullable=True)
    name          = db.Column(db.String(50), nullable=False)
    price_type    = db.Column(db.Enum("sales", "purchase"), nullable=False, default="sales")
    currency_id   = db.Column(db.Integer, db.ForeignKey("currency.id"), nullable=False)
    uom_id        = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=True)
    price         = db.Column(db.Numeric(18, 4), nullable=False)
    min_qty       = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    valid_from    = db.Column(db.Date, nullable=True)
    valid_to      = db.Column(db.Date, nullable=True)
    is_active     = db.Column(db.Boolean, default=True, nullable=False)

    currency   = db.relationship("Currency")
    uom        = db.relationship("StockUom")
    price_list = db.relationship("StockPriceList", foreign_keys=[price_list_id], back_populates="items")


class StockProductBundle(ArasModel):
    """Bundle — product composed of other products (kit/set)."""
    __tablename__ = "stock_product_bundle"
    __table_args__ = (
        db.UniqueConstraint("bundle_id", "component_id", name="uq_product_bundle_component"),
    )

    bundle_id    = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=False)
    qty          = db.Column(db.Numeric(12, 4), nullable=False, default=1)
    uom_id       = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=True)
    notes        = db.Column(db.String(255), nullable=True)

    component = db.relationship("StockProduct", foreign_keys=[component_id])
    uom       = db.relationship("StockUom")


class StockProductAccountLink(ArasModel):
    """Per-company COA mapping for a product (overrides category defaults)."""
    __tablename__ = "stock_product_account_link"
    __table_args__ = (
        db.UniqueConstraint("product_id", "company_id", name="uq_product_account_link"),
    )

    product_id          = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=False)
    company_id          = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    account_stock_id    = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    account_cogs_id     = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    account_revenue_id  = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    account_purchase_id = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)

    company          = db.relationship("Company")
    account_stock    = db.relationship("AccAccount", foreign_keys=[account_stock_id])
    account_cogs     = db.relationship("AccAccount", foreign_keys=[account_cogs_id])
    account_revenue  = db.relationship("AccAccount", foreign_keys=[account_revenue_id])
    account_purchase = db.relationship("AccAccount", foreign_keys=[account_purchase_id])
