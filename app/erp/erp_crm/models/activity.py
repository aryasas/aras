from arasCore.arasgen import ArasGen
from app.erp.erp_crm.manifest import Crm
from arasCore.lib.core.base_model import ArasModel, db


class CrmActivity(ArasGen.Model, module=Crm):
    __is_child__  = True
    __tablename__ = "crm_activity"
    __table_args__ = (
        db.Index("idx_crm_activity_lead", "lead_id", "date_due"),
        db.Index("idx_crm_activity_user", "assigned_to_id", "is_done"),
    )

    lead_id        = db.Column(db.Integer, db.ForeignKey("crm_lead.id"), nullable=False)
    type           = db.Column(db.Enum("call", "email", "meeting", "task", "note", "whatsapp"),
                               nullable=False, default="call")
    summary        = db.Column(db.String(255), nullable=False)
    description    = db.Column(db.Text, nullable=True)
    date_due       = db.Column(db.DateTime, nullable=True)
    date_done      = db.Column(db.DateTime, nullable=True)
    is_done        = db.Column(db.Boolean, default=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)

    assigned_to = db.relationship("User", foreign_keys=[assigned_to_id])
    lead = db.relationship("CrmLead", back_populates="activities")

    def __repr__(self):
        return f"<CrmActivity {self.type} lead={self.lead_id}>"
