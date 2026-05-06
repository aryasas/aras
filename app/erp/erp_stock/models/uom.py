from arasCore.lib.core.base_model import ArasModel, db


class StockUom(ArasModel):
    """Unit of Measure — e.g. pcs, kg, liter, box"""
    __tablename__ = "stock_uom"

    name = db.Column(db.String(50), nullable=False, unique=True)

