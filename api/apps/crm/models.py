from typing import Optional
from datetime import date
from sqlalchemy import String, ForeignKey, Boolean, Text, Float, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core import Aras
from core.response import ok, err
from core.exceptions import ValidationException
from apps.base import MasterDataBase, LineItemBase, ErpBase




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
    party_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_party_parties.id"), nullable=True)
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

    @Aras.model_action(name="convert", permission="edit", label="Convert to Party")
    def convert_to_party(self, db):
        from apps.party.models import Party

        # Check if already a party
        if self.party_id:
            raise ValidationException("Lead is already linked to a party.")

        # Create Party
        party = Party(
            org_id=self.org_id,
            name=self.name,
            email=self.contact_email,
            phone=self.contact_phone
        )
        db.add(party)
        db.flush()

        self.party_id = party.id
        self.status = "Won"
        self.lead_type = "Opportunity"
        # db.commit() # Removed

        return ok({"id": party.id}, message=f"Party {party.name} created successfully.")

class Activity(ErpBase):
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



