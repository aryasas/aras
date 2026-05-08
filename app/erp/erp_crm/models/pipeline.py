from arasCore.arasgen import ArasGen
from app.erp.erp_crm.manifest import Crm
from arasCore.lib.core.base_model import ArasModel, db


class CrmPipeline(ArasGen.Model, module=Crm):
    __title__     = "Pipelines"
    __icon__      = "fa-random"
    __menu_order__= 2
    __tablename__ = "crm_pipeline"

    company_id = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=False)
    name       = db.Column(db.String(100), nullable=False)

    stages = db.relationship("CrmStage", backref="pipeline", lazy="dynamic",
                             order_by="CrmStage.sequence", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CrmPipeline {self.name}>"


class CrmStage(ArasGen.Model, module=Crm):
    __is_child__  = True
    __tablename__ = "crm_stage"

    pipeline_id = db.Column(db.Integer, db.ForeignKey("crm_pipeline.id"), nullable=False)
    name        = db.Column(db.String(100), nullable=False)
    sequence    = db.Column(db.Integer, default=10)
    probability = db.Column(db.Numeric(5, 2), default=0)   # 0–100 %
    is_won      = db.Column(db.Boolean, default=False)
    is_lost     = db.Column(db.Boolean, default=False)
    fold_kanban = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<CrmStage {self.name}>"
