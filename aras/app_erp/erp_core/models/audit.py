from datetime import datetime
from arasCore.lib.extensions import db


class AuditLog(db.Model):
    """Immutable audit trail — never soft-deleted, no user tracking fields."""
    __tablename__ = "audit_log"
    __table_args__ = (
        db.Index("idx_audit_model", "model", "record_id"),
        db.Index("idx_audit_company", "company_id", "ts"),
    )

    id          = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    ts          = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id     = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)
    company_id  = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=True)
    model       = db.Column(db.String(100), nullable=False)
    record_id   = db.Column(db.Integer, nullable=True)
    action      = db.Column(db.String(20), nullable=False)  # create/update/delete/confirm/cancel/post
    before_json = db.Column(db.JSON, nullable=True)
    after_json  = db.Column(db.JSON, nullable=True)
    ip          = db.Column(db.String(45), nullable=True)
    user_agent  = db.Column(db.String(255), nullable=True)

    user = db.relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<AuditLog {self.action} {self.model}#{self.record_id}>"
