from arasCore.lib.base_model import ArasModel, db


class StockWarehouse(ArasModel):
    __tablename__ = "stock_warehouse"
    __table_args__ = (
        db.UniqueConstraint("company_id", "code", name="uq_stock_warehouse_code"),
    )

    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    code       = db.Column(db.String(10), nullable=False)
    name       = db.Column(db.String(100), nullable=False)
    address    = db.Column(db.Text)

    locations = db.relationship("StockLocation", backref="warehouse", cascade="all, delete-orphan")


class StockLocation(ArasModel):
    """Storage location inside a warehouse, supports hierarchy."""
    __tablename__ = "stock_location"

    warehouse_id  = db.Column(db.Integer, db.ForeignKey("stock_warehouse.id"), nullable=True)
    parent_id     = db.Column(db.Integer, db.ForeignKey("stock_location.id"), nullable=True)
    name          = db.Column(db.String(100), nullable=False)
    full_name     = db.Column(db.String(300))   # computed: WH/Zone/Rack
    location_type = db.Column(
        db.Enum("internal", "input", "output", "packing", "virtual", "customer", "vendor", "transit"),
        nullable=False, default="internal"
    )

    parent = db.relationship("StockLocation", remote_side="StockLocation.id", backref="children")
