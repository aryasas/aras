from typing import Optional
from sqlalchemy import String, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core import Aras
from ..base import MasterDataBase, LineItemBase

class Party(MasterDataBase):
    __tablename__ = "erp_party_parties"
    __unique_together__ = [("org_id", "code")]
    
    role: Mapped[str] = mapped_column(String(50), default="customer")
    role_label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    email: Mapped[str] = mapped_column(String(100), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    mobile: Mapped[str] = mapped_column(String(20), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    tax_id: Mapped[str] = mapped_column(String(20), nullable=True, info={"pattern": "^[0-9]{1,20}$"})
    pricelist_id: Mapped[int] = mapped_column(ForeignKey("erp_config_price_types.id"), nullable=True)
    
    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="parent", cascade="all, delete-orphan")

class Contact(LineItemBase):
    __tablename__ = "erp_party_contacts"
    __parent__ = "erp_party_parties"
    
    party_id: Mapped[int] = mapped_column(ForeignKey("erp_party_parties.id"))
    name: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(100), nullable=True)
    email: Mapped[str] = mapped_column(String(100), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    
    parent: Mapped["Party"] = relationship("Party", back_populates="contacts")
