from arasCore.arasgen import ArasGen
from app.erp.erp_main.manifest import Main
from arasCore.lib.core.base_model import ArasModel, db


class ErpNotification(ArasGen.Model, module=Main):
    __tablename__ = "main_notification"
    __table_args__ = (
        db.Index("idx_notif_user", "user_id", "is_read"),
    )

    user_id    = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=True)
    type       = db.Column(db.String(50), nullable=False)
    title      = db.Column(db.String(200), nullable=False)
    body       = db.Column(db.Text, nullable=True)
    url        = db.Column(db.String(500), nullable=True)
    is_read    = db.Column(db.Boolean, default=False)

    user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("erp_notifications", lazy="dynamic"))

    def __repr__(self):
        return f"<ErpNotification {self.type} user={self.user_id}>"


class EmailTemplate(ArasGen.Model, module=Main):
    __tablename__ = "main_email_template"

    company_id = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=True)
    code       = db.Column(db.String(100), nullable=False)
    name       = db.Column(db.String(150), nullable=False)
    subject    = db.Column(db.String(255), nullable=False)
    body_html  = db.Column(db.Text, nullable=True)
    body_text  = db.Column(db.Text, nullable=True)
    to_expr    = db.Column(db.String(500), nullable=True)
    cc_expr    = db.Column(db.String(500), nullable=True)
    bcc_expr   = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f"<EmailTemplate {self.code}>"
