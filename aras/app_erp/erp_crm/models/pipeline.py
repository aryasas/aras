from arasCore.lib.base_model import ArasModel, db


class CrmPipeline(ArasModel):
    __tablename__ = "crm_pipeline"

    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    name       = db.Column(db.String(100), nullable=False)

    stages = db.relationship("CrmStage", backref="pipeline", lazy="dynamic",
                             order_by="CrmStage.sequence", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CrmPipeline {self.name}>"


class CrmStage(ArasModel):
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
