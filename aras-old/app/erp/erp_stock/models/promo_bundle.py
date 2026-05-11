from arasCore.arasgen import ArasGen
from app.erp.erp_stock.manifest import Stock
from arasCore.lib.core.base_model import ArasModel, db


class StockPromoBundle(ArasGen.Model, module=Stock):
    __title__     = "Promo Bundles"
    __icon__      = "fa-gift"
    __menu_order__= 6
    """Promo bundle header — buy N items together at special prices."""
    __tablename__ = "stock_promo_bundle"

    price_type_id = db.Column(db.Integer, db.ForeignKey("stock_price_type.id"), nullable=True)
    name          = db.Column(db.String(100), nullable=False)
    valid_from    = db.Column(db.Date, nullable=True)
    valid_to      = db.Column(db.Date, nullable=True)
    is_active     = db.Column(db.Boolean, nullable=False, default=True)
    notes         = db.Column(db.Text, nullable=True)

    price_type = db.relationship("StockPriceType", foreign_keys=[price_type_id])
    items      = db.relationship("StockPromoBundleItem", back_populates="promo_bundle",
                                 cascade="all, delete-orphan")


class StockPromoBundleItem(ArasGen.Model, module=Stock):
    __is_child__  = True
    """Line item in a promo bundle — required product + promo price or discount."""
    __tablename__ = "stock_promo_bundle_item"

    promo_bundle_id = db.Column(db.Integer, db.ForeignKey("stock_promo_bundle.id"), nullable=False)
    product_id      = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=False)
    qty             = db.Column(db.Numeric(12, 4), nullable=False, default=1)
    uom_id          = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=True)
    promo_price     = db.Column(db.Numeric(18, 4), nullable=True)
    discount_pct    = db.Column(db.Numeric(5, 2), nullable=True)

    promo_bundle = db.relationship("StockPromoBundle", back_populates="items")
    product      = db.relationship("StockProduct", foreign_keys=[product_id])
    uom          = db.relationship("StockUom")
