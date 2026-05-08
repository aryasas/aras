from arasCore.arasgen import ArasGen
from app.erp.erp_config.manifest import Config
from arasCore.lib.core.base_model import ArasModel, db


class Attachment(ArasGen.Model, module=Config):
    __admin_list__= False
    __tablename__ = "cfg_attachment"
    __table_args__ = (
        db.Index("idx_attachment_target", "target_model", "target_id"),
    )

    company_id   = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=True)
    target_model = db.Column(db.String(100), nullable=True)
    target_id    = db.Column(db.Integer, nullable=True)
    filename     = db.Column(db.String(255), nullable=False)
    mime         = db.Column(db.String(100), nullable=True)
    size_bytes   = db.Column(db.Integer, nullable=True)
    storage      = db.Column(db.String(10), default="local")  # local/s3
    path         = db.Column(db.String(500), nullable=False)
    sha256       = db.Column(db.String(64), nullable=True)
    is_public    = db.Column(db.Boolean, default=False)
    uploaded_by  = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)

    uploader = db.relationship("User", foreign_keys=[uploaded_by])

    def __repr__(self):
        return f"<Attachment {self.filename}>"
