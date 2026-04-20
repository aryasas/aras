from arasCore.lib.base_model import ArasModel, db


class StockUomCategory(ArasModel):
    """UOM Category — groups UOMs that can be converted, e.g. Weight, Volume, Length"""
    __tablename__ = "stock_uom_category"

    name = db.Column(db.String(50), nullable=False, unique=True)


class StockUom(ArasModel):
    """Unit of Measure — e.g. pcs, kg, liter, box"""
    __tablename__ = "stock_uom"

    name        = db.Column(db.String(50), nullable=False, unique=True)
    code        = db.Column(db.String(10), nullable=False, unique=True)
    uom_type    = db.Column(db.Enum("reference", "smaller", "bigger"), nullable=False, default="reference")
    category_id = db.Column(db.Integer, db.ForeignKey("stock_uom_category.id"), nullable=False)
    ratio       = db.Column(db.Numeric(18, 6), nullable=False, default=1)
    rounding    = db.Column(db.Numeric(18, 6), nullable=False, default=0.01)

    category = db.relationship("StockUomCategory", backref="uoms")

    def to_base(self, qty):
        """Convert qty in this UOM to base/reference UOM qty."""
        return float(qty) * float(self.ratio)

    def from_base(self, qty):
        """Convert qty in base/reference UOM to this UOM."""
        return float(qty) / float(self.ratio) if self.ratio else 0


class StockUomConversion(ArasModel):
    """Explicit conversion factor between two UOMs in the same category."""
    __tablename__ = "stock_uom_conversion"
    __table_args__ = (
        db.UniqueConstraint("from_uom_id", "to_uom_id", name="uq_uom_conversion"),
    )

    from_uom_id = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=False)
    to_uom_id   = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=False)
    factor      = db.Column(db.Numeric(18, 6), nullable=False)

    from_uom = db.relationship("StockUom", foreign_keys=[from_uom_id])
    to_uom   = db.relationship("StockUom", foreign_keys=[to_uom_id])
