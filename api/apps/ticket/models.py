# gemini-flash
from typing import Optional, List
from datetime import date, datetime
from sqlalchemy import String, ForeignKey, Boolean, Text, Float, Date, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core import Aras
from core.response import ok
from core.base.orm import MasterDataBase, AuditedBase

# gemini-flash
class Team(MasterDataBase):
    __tablename__ = "ticket_teams"
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("core_users.id"), nullable=True)

# gemini-flash
class Category(MasterDataBase):
    __tablename__ = "ticket_categories"
    team_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ticket_teams.id"), nullable=True)
    sla_hours: Mapped[float] = mapped_column(Float, default=24)

# gemini-flash
class Ticket(AuditedBase):
    __tablename__ = "ticket_tickets"
    __features__ = ["audit", "workflow"]
    __workflow_states__ = ["Open", "In Progress", "Pending Customer", "Resolved", "Closed"]
    __scoped_by__ = [("org_id", "core_organizations")]

    org_id: Mapped[int] = mapped_column(Integer, ForeignKey("core_organizations.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="Open")
    
    subject: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ticket_type: Mapped[str] = mapped_column(String(20), default="Question", info={"choices": ["Question", "Bug", "Feature Request", "Complaint"]})
    priority: Mapped[str] = mapped_column(String(10), default="Normal", info={"choices": ["Low", "Normal", "High", "Critical"]})
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ticket_categories.id"), nullable=True)
    team_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ticket_teams.id"), nullable=True)
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("core_users.id"), nullable=True)
    requester_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    requester_email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    party_id: Mapped[Optional[int]] = mapped_column(ForeignKey("party_parties.id"), nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # unattributed (pre-tagging)
    @Aras.model_action(name="assign", permission="edit", label="Assign")
    def assign(self, db, assignee_id: int):
        self.assignee_id = assignee_id
        if self.status == "Open":
            self.status = "In Progress"
        return ok({"assignee_id": assignee_id})

    # unattributed (pre-tagging)
    @Aras.model_action(name="resolve", permission="edit", label="Resolve")
    def resolve(self, db):
        self.status = "Resolved"
        self.resolved_at = datetime.utcnow()
        return ok()

    # unattributed (pre-tagging)
    @Aras.model_action(name="close", permission="edit", label="Close")
    def close(self, db):
        self.status = "Closed"
        self.closed_at = datetime.utcnow()
        return ok()

    # unattributed (pre-tagging)
    @Aras.model_action(name="reopen", permission="edit", label="Reopen")
    def reopen(self, db):
        self.status = "Open"
        self.resolved_at = None
        self.closed_at = None
        return ok()

# gemini-flash
class TicketMessage(AuditedBase):
    __tablename__ = "ticket_messages"
    __parent__ = "ticket_tickets"
    ticket_id: Mapped[int] = mapped_column(ForeignKey("ticket_tickets.id"))
    body: Mapped[str] = mapped_column(Text)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False)
    author_id: Mapped[Optional[int]] = mapped_column(ForeignKey("core_users.id"), nullable=True)
    
    parent: Mapped["Ticket"] = relationship("Ticket", backref="messages")
