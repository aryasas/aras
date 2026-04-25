# -*- coding: utf-8 -*-
"""
arasCore/lib/script_models.py
DB model for server-side lifecycle scripts.
"""
from datetime import datetime
from arasCore.lib.extensions import db
from arasCore.lib.base_model import ArasModel


class SrvScript(ArasModel):
    """Python snippet attached to a resource lifecycle event."""
    __tablename__ = "srv_script"
    __table_args__ = (
        db.Index("idx_srv_script_resource", "app", "resource", "event"),
    )

    EVENTS = (
        "before_insert", "after_insert",
        "before_update", "after_update",
        "before_delete", "after_delete",
    )

    name     = db.Column(db.String(100), nullable=False)
    app      = db.Column(db.String(80),  nullable=False)
    resource = db.Column(db.String(100), nullable=False)
    event    = db.Column(db.String(30),  nullable=False)
    code     = db.Column(db.Text,        nullable=False, default="")
    active   = db.Column(db.Boolean,     default=True, nullable=False)
    created_at = db.Column(db.DateTime,  default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SrvScript {self.name} [{self.event}]>"
