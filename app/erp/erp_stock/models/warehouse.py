from arasCore.arasgen import ArasGen
from app.erp.erp_stock.manifest import Stock
from arasCore.lib.core.base_model import ArasModel, db


class StockLocation(ArasGen.Model, module=Stock):
    __title__     = "Locations"
    __icon__      = "fa-building-o"
    __menu_order__= 6
    """
    Storage location — supports full hierarchy (company → warehouse → zone → rack).
    location_type determines role:
      internal  = physical storage (gudang, rak) — holds real stock
      vendor    = virtual source for purchases
      customer  = virtual destination for sales/deliveries
      transit   = in-transit between locations
      virtual   = write-off, adjustment, opening balance
    """
    __tablename__ = "stock_location"
    __display_fields__ = ("name",)

    company_id    = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=True)
    parent_id     = db.Column(db.Integer, db.ForeignKey("stock_location.id"), nullable=True)
    name          = db.Column(db.String(100), nullable=False)
    full_name     = db.Column(db.String(300))   # computed: GU / Stok Utama / Rak A1
    code          = db.Column(db.String(20))
    location_type = db.Column(
        db.Enum("internal", "vendor", "customer", "transit", "virtual"),
        nullable=False, default="internal"
    )
    is_group      = db.Column(db.Boolean, default=False, nullable=False)

    parent   = db.relationship("StockLocation", remote_side="StockLocation.id", backref="children")


class StockProductLocation(ArasGen.Model, module=Stock):
    __is_child__  = True
    """Which locations stock a given product (min/max reorder levels per location)."""
    __tablename__ = "stock_product_location"
    __display_fields__ = ("product_id",)

    product_id  = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("stock_location.id"), nullable=False)
    min_qty     = db.Column(db.Numeric(12, 4), default=0)
    max_qty     = db.Column(db.Numeric(12, 4), default=0)
    notes       = db.Column(db.String(255))

    product  = db.relationship("StockProduct")
    location = db.relationship("StockLocation")
