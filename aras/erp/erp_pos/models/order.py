from datetime import datetime
from arasCore.lib.core.base_model import ArasModel, db


class PosOrder(ArasModel):
    __tablename__ = "pos_order"
    __table_args__ = (
        db.Index("idx_pos_order_session", "session_id", "state"),
        db.Index("idx_pos_order_customer", "customer_id"),
    )

    id           = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    session_id   = db.Column(db.Integer, db.ForeignKey("pos_session.id"), nullable=False)
    name         = db.Column(db.String(50), nullable=False)
    customer_id  = db.Column(db.Integer, db.ForeignKey("crm_customer.id"), nullable=True)
    cashier_id   = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    subtotal     = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    discount_amt = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    tax_amt      = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    total        = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    amount_paid  = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    change_amt   = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    state        = db.Column(db.Enum("draft", "paid", "invoiced", "cancelled"),
                             default="draft", nullable=False)
    note         = db.Column(db.Text, nullable=True)

    cashier  = db.relationship("User", foreign_keys=[cashier_id])
    customer = db.relationship("CrmCustomer")
    lines    = db.relationship("PosOrderLine", backref="order", lazy="dynamic",
                               cascade="all, delete-orphan")
    payments = db.relationship("PosPayment", backref="order", lazy="dynamic",
                               cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PosOrder {self.name} [{self.state}]>"


class PosOrderLine(ArasModel):
    __tablename__ = "pos_order_line"

    id           = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_id     = db.Column(db.BigInteger, db.ForeignKey("pos_order.id"), nullable=False)
    product_id   = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=True)
    product_name = db.Column(db.String(200), nullable=False)
    product_code = db.Column(db.String(50), nullable=True)
    uom_id       = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=True)
    qty          = db.Column(db.Numeric(12, 4), default=1, nullable=False)
    qty_base     = db.Column(db.Numeric(12, 6), default=0, nullable=False)
    unit_price   = db.Column(db.Numeric(18, 4), nullable=False)
    discount_pct = db.Column(db.Numeric(5, 2), default=0)
    tax_id       = db.Column(db.Integer, db.ForeignKey("charge.id"), nullable=True)
    tax_amt      = db.Column(db.Numeric(18, 4), default=0)
    subtotal     = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    note         = db.Column(db.String(255), nullable=True)

    product = db.relationship("StockProduct", foreign_keys=[product_id])
    uom     = db.relationship("StockUom", foreign_keys=[uom_id])

    def __repr__(self):
        return f"<PosOrderLine {self.product_name} x{self.qty}>"


class PosPayment(ArasModel):
    __tablename__ = "pos_payment"

    id        = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_id  = db.Column(db.BigInteger, db.ForeignKey("pos_order.id"), nullable=False)
    method    = db.Column(db.String(100), nullable=False, default="cash")
    amount    = db.Column(db.Numeric(18, 4), nullable=False)
    reference = db.Column(db.String(100), nullable=True)
    paid_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PosPayment {self.method} {self.amount}>"
