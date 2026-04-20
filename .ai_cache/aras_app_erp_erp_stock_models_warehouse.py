from arasCore.lib.extensions import db


class StockWarehouse(db.Model):
    __tablename__ = "stock_warehouse"
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey("core_company.id"), nullable=False)
    code       = db.Column(db.String(10), nullable=False)
    name       = db.Column(db.String(100), nullable=False)
    address    = db.Column(db.Text)
    is_active  = db.Column(db.Boolean, default=True, nullable=False)

    locations = db.relationship("StockLocation", backref="warehouse", cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint("company_id", "code", name="uq_stock_warehouse_code"),
    )


class StockLocation(db.Model):
    """Storage location inside a warehouse, supports hierarchy."""
    __tablename__ = "stock_location"
    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey("stock_warehouse.id"), nullable=True)
    parent_id    = db.Column(db.Integer, db.ForeignKey("stock_location.id"), nullable=True)
    name         = db.Column(db.String(100), nullable=False)
    full_name    = db.Column(db.String(300))   # computed: WH/Zone/Rack
    location_type = db.Column(
        db.Enum("internal", "input", "output", "packing", "virtual", "customer", "vendor", "transit"),
        nullable=False, default="internal"
    )
    is_active    = db.Column(db.Boolean, default=True, nullable=False)

    parent   = db.relationship("StockLocation", remote_side=[id], backref="children")
