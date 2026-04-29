# -*- coding: utf-8 -*-
"""
arasCore/lib/workflow_models.py
DB models for the workflow engine. Imported by workflow.py at runtime.
"""
from datetime import datetime
from arasCore.lib.core.extensions import db
from arasCore.lib.core.base_model import ArasModel


class WfState(ArasModel):
    """Current workflow state per object instance."""
    __tablename__ = "wf_state"

    definition_name = db.Column(db.String(100), nullable=False, index=True)
    object_id       = db.Column(db.Integer, nullable=False, index=True)
    current_state   = db.Column(db.String(100), nullable=False)
    updated_by_id   = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("definition_name", "object_id", name="uq_wf_state"),
    )


class WfHistory(ArasModel):
    """Full transition history."""
    __tablename__ = "wf_history"

    id              = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    definition_name = db.Column(db.String(100), nullable=False, index=True)
    object_id       = db.Column(db.Integer, nullable=False, index=True)
    from_state      = db.Column(db.String(100), nullable=False)
    to_state        = db.Column(db.String(100), nullable=False)
    action          = db.Column(db.String(100), nullable=False)
    user_id         = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)
    note            = db.Column(db.String(500), default="")
    created_at      = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
