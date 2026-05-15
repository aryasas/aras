from typing import Optional
from datetime import date
from sqlalchemy import String, ForeignKey, Boolean, Text, Float, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core import Aras
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

class Pipeline(MasterDataBase):
    __tablename__ = "erp_crm_pipelines"
    
    stages: Mapped[list["Stage"]] = relationship("Stage", back_populates="parent", cascade="all, delete-orphan")

class Stage(LineItemBase):
    __tablename__ = "erp_crm_stages"
    __parent__ = "erp_crm_pipelines"
    
    pipeline_id: Mapped[int] = mapped_column(ForeignKey("erp_crm_pipelines.id"))
    probability: Mapped[float] = mapped_column(Float, default=0)
    is_won: Mapped[bool] = mapped_column(Boolean, default=False)
    is_lost: Mapped[bool] = mapped_column(Boolean, default=False)
    
    parent: Mapped["Pipeline"] = relationship("Pipeline", back_populates="stages")

class Lead(MasterDataBase):
    __tablename__ = "erp_crm_leads"
    
    lead_type: Mapped[str] = mapped_column(String(20), default="Lead", info={"choices": ["Lead", "Opportunity"]})
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_crm_customers.id"), nullable=True)
    contact_name: Mapped[str] = mapped_column(String(200), nullable=True)
    contact_email: Mapped[str] = mapped_column(String(100), nullable=True)
    contact_phone: Mapped[str] = mapped_column(String(20), nullable=True)
    pipeline_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_crm_pipelines.id"), nullable=True)
    stage_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_crm_stages.id"), nullable=True)
    salesperson_id: Mapped[Optional[int]] = mapped_column(ForeignKey("auth_users.id"), nullable=True)
    expected_revenue: Mapped[float] = mapped_column(Float, default=0)
    probability: Mapped[float] = mapped_column(Float, default=0)
    priority: Mapped[str] = mapped_column(String(10), default="Normal", info={"choices": ["Low", "Normal", "High", "Very High"]})
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Open", info={"choices": ["Open", "Won", "Lost"]})

    @Aras.model_action(name="convert", permission="edit", label="Convert to Customer")
    def convert_to_customer(self):
        from sqlalchemy.orm import object_session
        from .models import Customer
        db = object_session(self)
        
        # Check if already a customer
        if self.customer_id:
            return {"error": "Lead is already linked to a customer."}
            
        # Create Customer
        customer = Customer(
            company_id=self.company_id,
            name=self.name,
            email=self.contact_email,
            phone=self.contact_phone,
            status="Active"
        )
        db.add(customer)
        db.flush()
        
        self.customer_id = customer.id
        self.status = "Won"
        self.lead_type = "Opportunity"
        db.commit()
        
        return {"id": customer.id, "message": f"Customer {customer.name} created successfully."}

class Activity(LineItemBase):
    __tablename__ = "erp_crm_activities"
    __parent__ = "erp_crm_leads"
    
    lead_id: Mapped[int] = mapped_column(ForeignKey("erp_crm_leads.id"))
    activity_type: Mapped[str] = mapped_column(String(20), default="Call", info={"choices": ["Call", "Email", "Meeting", "Task", "Note", "WhatsApp"]})
    summary: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date_due: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    assigned_to_id: Mapped[Optional[int]] = mapped_column(ForeignKey("auth_users.id"), nullable=True)
    
    parent: Mapped["Lead"] = relationship("Lead", backref="activities")



