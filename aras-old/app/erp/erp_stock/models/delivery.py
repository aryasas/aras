from arasCore.arasgen import ArasGen
from app.erp.erp_stock.manifest import Stock
from arasCore.lib.core.base_model import ArasModel, db


class DeliveryTrip(ArasGen.Model, module=Stock):
    __title__     = "Delivery Trips"
    __icon__      = "fa-road"
    __menu_order__= 6
    """Delivery trip — groups multiple delivery orders for one vehicle/driver/date."""
    __tablename__ = "stk_delivery_trip"
    __table_args__ = (
        db.Index("ix_dtrip_company_date", "company_id", "trip_date"),
    )

    id         = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=False)
    name       = db.Column(db.String(50), nullable=False)   # DT/2024/0001
    trip_date  = db.Column(db.Date, nullable=False)
    driver_name = db.Column(db.String(200), nullable=True)
    vehicle_no  = db.Column(db.String(50), nullable=True)
    state       = db.Column(db.Enum("draft", "in_progress", "completed", "cancelled"),
                             default="draft", nullable=False)
    notes       = db.Column(db.Text, nullable=True)

    company = db.relationship("Company")
    orders  = db.relationship("DeliveryOrder", back_populates="trip")

    def __repr__(self):
        return f"<DeliveryTrip {self.name} [{self.state}]>"


class DeliveryOrder(ArasGen.Model, module=Stock):
    __title__     = "Delivery Orders"
    __icon__      = "fa-map-marker"
    __menu_order__= 6
    """Delivery order — one delivery to one customer address."""
    __tablename__ = "stk_delivery_order"
    __table_args__ = (
        db.Index("ix_do_company_date", "company_id", "delivery_date"),
        db.Index("ix_do_state", "state"),
    )

    id               = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    company_id       = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=False)
    name             = db.Column(db.String(50), nullable=False)   # DO/2024/0001
    sales_invoice_id = db.Column(db.BigInteger, db.ForeignKey("acc_sales_invoice.id"), nullable=True)
    sales_order_id   = db.Column(db.BigInteger, db.ForeignKey("acc_sales_order.id"), nullable=True)
    customer_id      = db.Column(db.Integer, db.ForeignKey("crm_customer.id"), nullable=True)
    src_location_id  = db.Column(db.Integer, db.ForeignKey("stock_location.id"), nullable=True)
    delivery_date    = db.Column(db.Date, nullable=True)
    state            = db.Column(db.Enum("draft", "assigned", "in_transit", "delivered", "cancelled"),
                                  default="draft", nullable=False)
    notes            = db.Column(db.Text, nullable=True)
    trip_id          = db.Column(db.BigInteger, db.ForeignKey("stk_delivery_trip.id"), nullable=True)

    company       = db.relationship("Company")
    sales_invoice = db.relationship("AccSalesInvoice", foreign_keys=[sales_invoice_id])
    sales_order   = db.relationship("SalesOrder", foreign_keys=[sales_order_id])
    customer      = db.relationship("CrmCustomer")
    src_location  = db.relationship("StockLocation", foreign_keys=[src_location_id])
    lines         = db.relationship("DeliveryOrderLine", back_populates="delivery",
                                     cascade="all, delete-orphan")
    trip          = db.relationship("DeliveryTrip", back_populates="orders")

    def __repr__(self):
        return f"<DeliveryOrder {self.name} [{self.state}]>"


class DeliveryOrderLine(ArasGen.Model, module=Stock):
    __is_child__  = True
    __tablename__ = "stk_delivery_order_line"

    id          = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    delivery_id = db.Column(db.BigInteger, db.ForeignKey("stk_delivery_order.id"), nullable=False)
    product_id  = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=True)
    description = db.Column(db.String(255), nullable=False)
    qty         = db.Column(db.Numeric(12, 4), default=1, nullable=False)
    uom_id      = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=True)
    notes       = db.Column(db.String(255), nullable=True)

    product = db.relationship("StockProduct")
    uom     = db.relationship("StockUom")
    delivery = db.relationship("DeliveryOrder", back_populates="lines")
