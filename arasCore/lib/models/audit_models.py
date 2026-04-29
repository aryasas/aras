# -*- coding: utf-8 -*-
"""
arasCore/lib/audit_models.py
DB model for field-level audit log. Imported lazily by audit.py.
"""
from datetime import datetime
from arasCore.lib.core.extensions import db
from arasCore.lib.core.base_model import ArasModel


class AuditFieldLog(ArasModel):
    """One row per field change. Opt-in via __audit_fields__ = True."""
    __tablename__ = "audit_field_log"
    __table_args__ = (
        db.Index("idx_audit_field", "resource", "object_id"),
    )

    id            = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    app           = db.Column(db.String(80),  nullable=False)
    resource      = db.Column(db.String(100), nullable=False)
    object_id     = db.Column(db.Integer,     nullable=True)
    field_name    = db.Column(db.String(100), nullable=False)
    old_value     = db.Column(db.Text, nullable=True)
    new_value     = db.Column(db.Text, nullable=True)
    changed_by_id = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)
    changed_at    = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
