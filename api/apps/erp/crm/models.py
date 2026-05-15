from sqlalchemy import String, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base import MasterDataBase, LineItemBase

class Customer(MasterDataBase):
    __tablename__ = "erp_crm_customers"
    __unique_together__ = [("company_id", "code")]
    
    email: Mapped[str] = mapped_column(String(100), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    mobile: Mapped[str] = mapped_column(String(20), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    tax_id: Mapped[str] = mapped_column(String(50), nullable=True)
    pricelist_id: Mapped[int] = mapped_column(ForeignKey("erp_config_price_types.id"), nullable=True)
    
    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="parent", cascade="all, delete-orphan")

class Contact(LineItemBase):
    __tablename__ = "erp_crm_contacts"
    __parent__ = "erp_crm_customers"
    
    customer_id: Mapped[int] = mapped_column(ForeignKey("erp_crm_customers.id"))
    name: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(100), nullable=True)
    email: Mapped[str] = mapped_column(String(100), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    
    parent: Mapped["Customer"] = relationship("Customer", back_populates="contacts")
