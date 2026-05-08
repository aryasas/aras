from arasCore.arasgen import ArasGen
from app.erp.erp_sup.manifest import Sup
from arasCore.lib.core.base_model import ArasModel, db


class PurchaseOrder(ArasGen.Model, module=Sup):
    __title__     = "Purchase Orders"
    __icon__      = "fa-shopping-basket"
    __menu_order__= 3
    __tablename__ = "sup_purchase_order"
    __table_args__ = (
        db.Index("ix_po_company_date", "company_id", "order_date"),
        db.Index("ix_po_supplier", "supplier_id"),
        db.Index("ix_po_state", "state"),
    )

    id            = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    company_id    = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=False)
    name          = db.Column(db.String(50), nullable=False)
    supplier_id   = db.Column(db.Integer, db.ForeignKey("sup_supplier.id"), nullable=True)
    location_id   = db.Column(db.Integer, db.ForeignKey("stock_location.id"), nullable=True)
    order_date    = db.Column(db.Date, nullable=False)
    expected_date = db.Column(db.Date, nullable=True)
    currency_id   = db.Column(db.Integer, db.ForeignKey("cfg_currency.id"), nullable=False)
    price_type_id = db.Column(db.Integer, db.ForeignKey("stock_price_type.id"), nullable=True)
    subtotal      = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    discount_amt  = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    charge_amt    = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    total         = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    state         = db.Column(db.Enum("draft", "confirmed", "partial", "closed", "cancelled"),
                               default="draft", nullable=False)
    reference     = db.Column(db.String(100), nullable=True)
    notes         = db.Column(db.Text, nullable=True)

    company    = db.relationship("Company")
    supplier   = db.relationship("SupSupplier", foreign_keys=[supplier_id])
    location   = db.relationship("StockLocation", foreign_keys=[location_id])
    currency   = db.relationship("Currency")
    price_type = db.relationship("StockPriceType", foreign_keys=[price_type_id])
    lines      = db.relationship("PurchaseOrderLine", back_populates="order",
                                  cascade="all, delete-orphan")
    charges    = db.relationship("PurchaseOrderCharge", back_populates="order",
                                  cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PurchaseOrder {self.name} [{self.state}]>"

    def detail_context(self, obj):
        if not obj:
            return {}
        if obj.state == "confirmed":
            return {
                "post_url": "/api/erp/sup/purchase_order/create_invoice_from_order/",
                "obj_id":   obj.id,
            }
        return {"obj_state": obj.state}

class PurchaseOrderLine(ArasGen.Model, module=Sup):
    __is_child__  = True
    __tablename__ = "sup_purchase_order_line"

    id            = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_id      = db.Column(db.BigInteger, db.ForeignKey("sup_purchase_order.id"), nullable=False)
    sequence      = db.Column(db.Integer, default=0)
    product_id    = db.Column(db.Integer, db.ForeignKey("stock_product.id"), nullable=True)
    description   = db.Column(db.String(255), nullable=False)
    qty           = db.Column(db.Numeric(12, 4), default=1, nullable=False)
    qty_received  = db.Column(db.Numeric(12, 4), default=0, nullable=False)
    uom_id        = db.Column(db.Integer, db.ForeignKey("stock_uom.id"), nullable=True)
    unit_price    = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    discount_pct  = db.Column(db.Numeric(5, 2), default=0, nullable=False)
    subtotal      = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    account_id    = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)

    product = db.relationship("StockProduct")
    uom     = db.relationship("StockUom")
    account = db.relationship("AccAccount")
    order   = db.relationship("PurchaseOrder", back_populates="lines")


class PurchaseOrderCharge(ArasGen.Model, module=Sup):
    __is_child__  = True
    __tablename__ = "sup_purchase_order_charge"

    id         = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    order_id   = db.Column(db.BigInteger, db.ForeignKey("sup_purchase_order.id"), nullable=False)
    charge_id  = db.Column(db.Integer, db.ForeignKey("cfg_charge.id"), nullable=False)
    sequence   = db.Column(db.Integer, default=10)
    base_amt   = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    amount     = db.Column(db.Numeric(18, 4), default=0, nullable=False)
    account_id = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)

    charge  = db.relationship("Charge")
    account = db.relationship("AccAccount")
    order   = db.relationship("PurchaseOrder", back_populates="charges")
