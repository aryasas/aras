from arasCore.arasgen import ArasGen
from app.erp.erp_stock.manifest import Stock
from arasCore.lib.core.base_model import ArasModel, db


class StockUom(ArasGen.Model, module=Stock):
    __title__     = "Units of Measure"
    __icon__      = "fa-balance-scale"
    __menu_order__= 6
    """Unit of Measure — e.g. pcs, kg, liter, box"""
    __tablename__ = "stock_uom"

    name = db.Column(db.String(50), nullable=False, unique=True)

