# -*- coding: utf-8 -*-
"""
arasCore/lib/webhook_models.py
DB model for webhook endpoint registration.
"""
from datetime import datetime
from arasCore.lib.core.extensions import db
from arasCore.lib.core.base_model import ArasModel


class WebhookEndpoint(ArasModel):
    """A registered outbound webhook. Fired on matching framework events."""
    __tablename__ = "wh_endpoint"

    name       = db.Column(db.String(100), nullable=False)
    url        = db.Column(db.String(500), nullable=False)
    event      = db.Column(db.String(200), nullable=False)  # e.g. "erp/acc_journal.created" or "*"
    secret     = db.Column(db.String(200), nullable=True)   # used for HMAC-SHA256 signature
    active     = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<WebhookEndpoint {self.name} → {self.event}>"
