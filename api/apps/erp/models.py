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
