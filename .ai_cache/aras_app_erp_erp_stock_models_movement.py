from arasCore.lib.extensions import db


MOVE_TYPES = ["receipt", "delivery", "internal", "adjustment", "opening", "return", "scrap"]


class StockMovement(db.Model):
    """
    Stock movement document (header).
    One movement auto-creates one AccJournalEntry on post.
    origin_model + origin_id links back to source (PO, SO, POS Order, etc.)
    """
    __tablename__ = "stock_movement"
    id               = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    company_id       = db.Column(db.Integer, db.ForeignKey("core_company.id"), nullable=False)
    name             = db.Column(db.String(50), nullable=False)   # sequence: SM/2024/0001
    move_type        = db.Column(db.Enum(*MOVE_TYPES), nullable=False)
    state            = db.Column(db.Enum("draft", "confirmed", "posted", "cancelled"), nullable=False, default="draft")
    date_move        = db.Column(db.Date, nullable=False)
    src_location_id  = db.Column(db.Integer, db.ForeignKey("stock_location.id"), nullable=True)
    dst_location_id  = db.Column(db.Integer, db.ForeignKey("stock_location.id"), nullable=True)
    reference        = db.Column(db.String(100))
    notes            = db.Column(db.Text)
    # Link to accounting — set when posted
    journal_entry_id = db.Column(db.BigInteger, db.ForeignKey("acc_journal_entry.id"), nullable=True)
    # Source document
    origin_model     = db.Column(db.String(50))
    origin_id        = db.Column(db.BigInteger)
    fiscal_period_id = db.Column(db.Integer, db.ForeignKey("core_fiscal_period.id"), nullable=True)
    created_at       = db.Column(db.DateTime, server_default=db.func.now())
    updated_at       = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    created_by       = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)

    lines         = db.relationship("StockMovementLine", backref="movement", cascade="all, delete-orphan")
    src_location  = db.relationship("StockLocation", foreign_keys=[src_location_id])
    dst_location  = db.relationship("StockLocation", foreign_keys=[dst_location_id])
    journal_entry = db.relationship("AccJournalEntry", foreign_keys=[journal_entry_id])

    __table_args__ = (
        db.Index("ix_stock_move_company_date", "company_id", "date_move"),
        db.Index("ix_stock_move_origin", "origin_model", "origin_id"),
    )


class StockMovementLine(db.Model):
    """One product line in a movement."""
    __tablename__ = "stock_movement_line"
    id            = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    movement_id   = db.Column(db.BigInteger, db.ForeignKey("stock_movement.id"), nullable=False)
    product_id    = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=False)
    uom_id        = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=False)
    qty           = db.Column(db.Numeric(18, 4), nullable=False)
    qty_base      = db.Column(db.Numeric(18, 4), nullable=False)   # qty converted to base UOM
    unit_cost     = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    total_cost    = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    lot_number    = db.Column(db.String(50))
    serial_number = db.Column(db.String(100))
    notes         = db.Column(db.String(200))

    product = db.relationship("StockProduct")
    uom     = db.relationship("StockUom")


class StockValuation(db.Model):
    """
    Running stock balance per product per location.
    Updated on every posted movement.
    """
    __tablename__ = "stock_valuation"
    id          = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    company_id  = db.Column(db.Integer, db.ForeignKey("core_company.id"), nullable=False)
    product_id  = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("stock_location.id"), nullable=False)
    qty_on_hand = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    avg_cost    = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    total_value = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    updated_at  = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    product  = db.relationship("StockProduct")
    location = db.relationship("StockLocation")

    __table_args__ = (
        db.UniqueConstraint("company_id", "product_id", "location_id", name="uq_stock_valuation"),
    )
