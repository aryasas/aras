from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from core import Aras

class Product(Aras.Model):
    __tablename__ = "erp_products"
    __features__ = ["audit"]

    name: Mapped[str] = mapped_column(String(100), unique=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True)
    price: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    stock_quantity: Mapped[float] = mapped_column(Float, default=0)

class Customer(Aras.Model):
    __tablename__ = "erp_customers"
    __features__ = ["audit"]

    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    address: Mapped[str] = mapped_column(String(255), nullable=True)

class Order(Aras.Model):
    __tablename__ = "erp_orders"
    __features__ = ["audit", "workflow"]
    __workflow__ = True

    number: Mapped[str] = mapped_column(String(20), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="Draft", server_default="Draft")
    customer_id: Mapped[int] = mapped_column(ForeignKey("erp_customers.id"))
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    rejection_reason: Mapped[str] = mapped_column(String(255), nullable=True, info={"depends_on": "status=Rejected"})

    __layout__ = [
        {"title": "General Information", "fields": ["number", "customer_id", "status"]},
        {"title": "Financials", "fields": ["total_amount", "rejection_reason"]}
    ]

    __transitions__ = [
        {"from": "Draft", "to": "Confirmed", "label": "Confirm Order"},
        {"from": "Confirmed", "to": "Rejected", "label": "Reject Order"},
        {"from": "Confirmed", "to": "Shipped", "label": "Mark as Shipped"}
    ]

    @Aras.action(name="recalculate", permission="edit", label="Recalculate Totals")
    def recalculate(self):
        self.total_amount = 99.99 # Dummy logic
        return True

