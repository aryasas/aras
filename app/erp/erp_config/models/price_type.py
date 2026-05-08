from arasCore.arasgen import ArasGen
from app.erp.erp_config.manifest import Config
from arasCore.lib.core.base_model import db


class StockPriceType(ArasGen.Model, module=Config):
    __title__     = "Price Types"
    __icon__      = "fa-tag"
    __menu_order__= 7
    __display_fields__ = ("name",)
    """Named price group/reference — e.g. Retail, Wholesale, Promo A."""
    __tablename__ = "stock_price_type"
    __table_args__ = (
        db.UniqueConstraint("company_id", "name", name="uq_price_type_company_name"),
    )

    company_id  = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=False)
    name        = db.Column(db.String(100), nullable=False)
    price_type  = db.Column(db.Enum("sales", "purchase"), nullable=False, default="sales")
    currency_id = db.Column(db.Integer, db.ForeignKey("cfg_currency.id"), nullable=False)
    description = db.Column(db.Text)

    currency = db.relationship("Currency")
    items    = db.relationship("StockPriceList",
                               foreign_keys="StockPriceList.price_type_id",
                               back_populates="price_type_ref",
                               cascade="all, delete-orphan")
