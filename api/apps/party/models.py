from typing import Optional
from sqlalchemy import String, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core import Aras
from core.base.orm import MasterDataBase, AuditedBase
from core.base.field import Field

# gpt-5
class Party(MasterDataBase):
    __tablename__ = "party_parties"
    __unique_together__ = [("org_id", "code")]
    __soft_delete__ = True

    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="customer", info={"choices": ["customer", "supplier", "employee", "agent", "partner"]})
    role_label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    email: Mapped[str] = Field(String(100), nullable=True, pii=True)
    phone: Mapped[str] = Field(String(20), nullable=True, pii=True)
    mobile: Mapped[str] = Field(String(20), nullable=True, pii=True)
    address: Mapped[str] = Field(Text, nullable=True, pii=True)
    tax_id: Mapped[str] = mapped_column(String(20), nullable=True, info={"pattern": "^[0-9]{1,20}$"})
    pricelist_id: Mapped[int] = mapped_column(ForeignKey("config_price_types.id"), nullable=True)
    
    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="parent", cascade="all, delete-orphan")

# gpt-5
class Contact(AuditedBase):
    __tablename__ = "party_contacts"
    __parent__ = "party_parties"
    
    party_id: Mapped[int] = mapped_column(ForeignKey("party_parties.id"))
    name: Mapped[str] = Field(String(200), pii=True)
    title: Mapped[str] = mapped_column(String(100), nullable=True)
    email: Mapped[str] = Field(String(100), nullable=True, pii=True)
    phone: Mapped[str] = Field(String(20), nullable=True, pii=True)
    address: Mapped[str] = Field(Text, nullable=True, pii=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    
    parent: Mapped["Party"] = relationship("Party", back_populates="contacts")
