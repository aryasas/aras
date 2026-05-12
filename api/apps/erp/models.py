from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped
from core import Aras

class Product(Aras.Model):
    __tablename__ = "erp_products"
    __title__ = "Product Catalog"
    __features__ = ["audit"]

    name: Mapped[str] = Aras.Column(String(100), unique=True, label="Product Name", searchable=True)
    sku: Mapped[str] = Aras.Column(String(50), unique=True, label="SKU / Item Code")
    price: Mapped[float] = Aras.Column(Float, label="Standard Price", ui_type="currency")
    description: Mapped[str] = Aras.Column(String(255), nullable=True, label="Description", ui_type="textarea")
    stock_quantity: Mapped[float] = Aras.Column(Float, default=0, label="Current Stock")

class Customer(Aras.Model):
    __tablename__ = "erp_customers"
    __title__ = "Customer Relationship"
    __features__ = ["audit"]

    name: Mapped[str] = Aras.Column(String(100), label="Customer Name", searchable=True)
    email: Mapped[str] = Aras.Column(String(100), nullable=True, label="Email", ui_type="email")
    phone: Mapped[str] = Aras.Column(String(20), nullable=True, label="Phone")
    address: Mapped[str] = Aras.Column(String(255), nullable=True, label="Address", ui_type="textarea")
