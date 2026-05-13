from core import Aras
from pydantic import field_validator
from typing import Optional, ClassVar, Any

class ProductSchema(Aras.Schema):
    model: ClassVar[Any] = "erp_products"
    
    name: str
    sku: str
    price: float
    description: Optional[str] = None
    stock_quantity: float = 0

    @field_validator('price')
    @classmethod
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be a positive number')
        return v

    @field_validator('sku')
    @classmethod
    def validate_sku(cls, v):
        if len(v) < 3:
            raise ValueError('SKU must be at least 3 characters long')
        return v

class CustomerSchema(Aras.Schema):
    model: ClassVar[Any] = "erp_customers"
    
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v and "@" not in v:
            raise ValueError('Invalid email format')
        return v
