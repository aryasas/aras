from datetime import datetime
from arasCore.lib.extensions import db


class SocReport(db.Model):
    __tablename__ = "soc_report"

    id              = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    reporter_id     = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    target_type     = db.Column(db.String(10), nullable=False)   # post/comment/user
    target_id       = db.Column(db.BigInteger, nullable=False)
    reason          = db.Column(db.String(30), nullable=False)
    description     = db.Column(db.Text, nullable=True)
    status          = db.Column(db.String(10), default="pending")  # pending/reviewed/resolved/dismissed
    reviewed_by_id  = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)
    reviewed_at     = db.Column(db.DateTime, nullable=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at      = db.Column(db.DateTime, nullable=True)

    reporter    = db.relationship("User", foreign_keys=[reporter_id])
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id])

    def __repr__(self):
        return f"<SocReport {self.target_type}={self.target_id} [{self.status}]>"
