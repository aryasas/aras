from arasCore.arasgen import ArasGen
from app.erp.erp_crm.manifest import Crm
from arasCore.lib.core.base_model import ArasSoftModel, db


class CrmLead(ArasGen.Model, module=Crm):
    __title__     = "Leads"
    __icon__      = "fa-filter"
    __menu_order__= 2
    """Lead / Opportunity unified model. type='lead' before qualification, 'opportunity' after."""
    __tablename__ = "crm_lead"
    __table_args__ = (
        db.Index("idx_crm_lead_stage", "stage_id", "type"),
        db.Index("idx_crm_lead_salesperson", "salesperson_id", "company_id"),
    )

    company_id       = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=False)
    type             = db.Column(db.Enum("lead", "opportunity"), default="lead", nullable=False)
    name             = db.Column(db.String(255), nullable=False)
    customer_id      = db.Column(db.Integer, db.ForeignKey("crm_customer.id"), nullable=True)
    contact_name     = db.Column(db.String(200), nullable=True)
    contact_email    = db.Column(db.String(120), nullable=True)
    contact_phone    = db.Column(db.String(50), nullable=True)
    pipeline_id      = db.Column(db.Integer, db.ForeignKey("crm_pipeline.id"), nullable=True)
    stage_id         = db.Column(db.Integer, db.ForeignKey("crm_stage.id"), nullable=True)
    salesperson_id   = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)
    expected_revenue = db.Column(db.Numeric(18, 4), default=0)
    probability      = db.Column(db.Numeric(5, 2), default=0)
    priority         = db.Column(db.Enum("0", "1", "2", "3"), default="0")  # normal/low/high/very high
    source           = db.Column(db.String(100), nullable=True)
    campaign         = db.Column(db.String(100), nullable=True)
    medium           = db.Column(db.String(100), nullable=True)
    description      = db.Column(db.Text, nullable=True)
    date_deadline    = db.Column(db.Date, nullable=True)
    date_closed      = db.Column(db.DateTime, nullable=True)
    lost_reason      = db.Column(db.String(255), nullable=True)
    state            = db.Column(db.Enum("open", "won", "lost"), default="open", nullable=False)

    customer    = db.relationship("CrmCustomer", backref=db.backref("leads", lazy="dynamic"))
    stage       = db.relationship("CrmStage")
    pipeline    = db.relationship("CrmPipeline")
    salesperson = db.relationship("User", foreign_keys=[salesperson_id])
    activities  = db.relationship("CrmActivity", backref="lead", lazy="dynamic",
                                  cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CrmLead {self.name} [{self.state}]>"

    def detail_context(self, obj):
        if not obj or obj.state == "won":
            return {}
        return {"convert_url": "/api/erp/crm/lead/convert_to_customer/"}

