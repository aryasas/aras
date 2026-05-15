from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from ..base import MasterDataBase

class Supplier(MasterDataBase):
    __tablename__ = "erp_supplier_suppliers"
    __unique_together__ = [("company_id", "code")]
    
    email: Mapped[str] = mapped_column(String(100), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    mobile: Mapped[str] = mapped_column(String(20), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    tax_id: Mapped[str] = mapped_column(String(50), nullable=True)
