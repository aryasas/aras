from arasCore.lib.extensions import db


class StockProductCategory(db.Model):
    __tablename__ = "stock_product_category"
    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name           = db.Column(db.String(100), nullable=False)
    parent_id      = db.Column(db.Integer, db.ForeignKey("stock_product_category.id"), nullable=True)
    account_stock_id        = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    account_cogs_id         = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    account_revenue_id      = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    account_purchase_id     = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    account_variance_id     = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    valuation_method        = db.Column(db.Enum("standard", "average", "fifo"), nullable=False, default="average")
    is_active               = db.Column(db.Boolean, default=True, nullable=False)

    parent   = db.relationship("StockProductCategory", remote_side=[id], backref="children")
    account_stock    = db.relationship("AccAccount", foreign_keys=[account_stock_id])
    account_cogs     = db.relationship("AccAccount", foreign_keys=[account_cogs_id])
    account_revenue  = db.relationship("AccAccount", foreign_keys=[account_revenue_id])
    account_purchase = db.relationship("AccAccount", foreign_keys=[account_purchase_id])
    account_variance = db.relationship("AccAccount", foreign_keys=[account_variance_id])


class StockProduct(db.Model):
    __tablename__ = "stock_product"
    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id      = db.Column(db.Integer, db.ForeignKey("core_company.id"), nullable=False)
    code            = db.Column(db.String(50), nullable=False)
    name            = db.Column(db.String(200), nullable=False)
    description     = db.Column(db.Text)
    category_id     = db.Column(db.Integer, db.ForeignKey("stock_product_category.id"), nullable=True)
    uom_id          = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=False)
    uom_purchase_id = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=True)
    uom_sales_id    = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=True)
    product_type    = db.Column(db.Enum("storable", "consumable", "service"), nullable=False, default="storable")
    barcode         = db.Column(db.String(100), nullable=True)
    cost_price      = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    standard_price  = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    # Sales / purchase flags — controls visibility in POS and purchasing
    for_sales       = db.Column(db.Boolean, default=True, nullable=False)
    for_purchase    = db.Column(db.Boolean, default=True, nullable=False)
    is_active       = db.Column(db.Boolean, default=True, nullable=False)
    created_at      = db.Column(db.DateTime, server_default=db.func.now())
    updated_at      = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    __table_args__ = (
        db.UniqueConstraint("company_id", "code", name="uq_stock_product_company_code"),
    )

    category     = db.relationship("StockProductCategory")
    uom          = db.relationship("StockUom", foreign_keys=[uom_id])
    uom_purchase = db.relationship("StockUom", foreign_keys=[uom_purchase_id])
    uom_sales    = db.relationship("StockUom", foreign_keys=[uom_sales_id])
    uom_alts     = db.relationship("StockProductUom", backref="product", cascade="all, delete-orphan")
    price_lists  = db.relationship("StockPriceListItem", backref="product", cascade="all, delete-orphan")
    prices       = db.relationship("StockProductPrice", backref="product", cascade="all, delete-orphan")
    account_links = db.relationship("StockProductAccountLink", backref="product", cascade="all, delete-orphan")
    bundle_components = db.relationship(
        "StockProductBundle", foreign_keys="StockProductBundle.bundle_id",
        backref="bundle", cascade="all, delete-orphan"
    )


class StockProductUom(db.Model):
    """Alternative UOMs for a product with per-product conversion factor."""
    __tablename__ = "stock_product_uom"
    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id  = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=False)
    uom_id      = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=False)
    factor      = db.Column(db.Numeric(18, 6), nullable=False)
    barcode     = db.Column(db.String(100), nullable=True)
    is_active   = db.Column(db.Boolean, default=True, nullable=False)

    uom = db.relationship("StockUom")

    __table_args__ = (
        db.UniqueConstraint("product_id", "uom_id", name="uq_stock_product_uom"),
    )


class StockProductPrice(db.Model):
    """Direct price table per product — multiple price levels (Retail, Wholesale, etc.)."""
    __tablename__ = "stock_product_price"
    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id  = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=False)
    name        = db.Column(db.String(50), nullable=False)   # e.g. "Retail", "Wholesale"
    price_type  = db.Column(db.Enum("sales", "purchase"), nullable=False, default="sales")
    currency_id = db.Column(db.Integer, db.ForeignKey("core_currency.id"), nullable=False)
    uom_id      = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=True)
    price       = db.Column(db.Numeric(18, 4), nullable=False)
    min_qty     = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    valid_from  = db.Column(db.Date, nullable=True)
    valid_to    = db.Column(db.Date, nullable=True)
    is_active   = db.Column(db.Boolean, default=True, nullable=False)

    currency = db.relationship("CoreCurrency")
    uom      = db.relationship("StockUom")


class StockProductBundle(db.Model):
    """Bundle — product that is composed of other products (kit/set)."""
    __tablename__ = "stock_product_bundle"
    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bundle_id     = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=False)
    component_id  = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=False)
    qty           = db.Column(db.Numeric(12, 4), nullable=False, default=1)
    uom_id        = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=True)
    notes         = db.Column(db.String(255), nullable=True)

    component = db.relationship("StockProduct", foreign_keys=[component_id])
    uom       = db.relationship("StockUom")

    __table_args__ = (
        db.UniqueConstraint("bundle_id", "component_id", name="uq_product_bundle_component"),
    )


class StockProductAccountLink(db.Model):
    """Per-company COA mapping for a product (overrides category defaults)."""
    __tablename__ = "stock_product_account_link"
    id               = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id       = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=False)
    company_id       = db.Column(db.Integer, db.ForeignKey("core_company.id"), nullable=False)
    account_stock_id    = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    account_cogs_id     = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    account_revenue_id  = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    account_purchase_id = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)

    company          = db.relationship("CoreCompany")
    account_stock    = db.relationship("AccAccount", foreign_keys=[account_stock_id])
    account_cogs     = db.relationship("AccAccount", foreign_keys=[account_cogs_id])
    account_revenue  = db.relationship("AccAccount", foreign_keys=[account_revenue_id])
    account_purchase = db.relationship("AccAccount", foreign_keys=[account_purchase_id])

    __table_args__ = (
        db.UniqueConstraint("product_id", "company_id", name="uq_product_account_link"),
    )
