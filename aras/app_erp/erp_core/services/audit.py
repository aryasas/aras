"""core.audit — write to core_audit_log."""
import json
from datetime import datetime
from flask import request
from flask_login import current_user
from arasCore.lib.extensions import db
from aras.app_erp.erp_core.models.audit import CoreAuditLog


def log(model: str, record_id, action: str,
        before=None, after=None, company_id: int = None):
    user_id = None
    try:
        if current_user and current_user.is_authenticated:
            user_id = current_user.id
    except RuntimeError:
        pass

    ip = None
    ua = None
    try:
        ip = request.remote_addr
        ua = request.user_agent.string[:255] if request.user_agent else None
    except RuntimeError:
        pass

    entry = CoreAuditLog(
        ts=datetime.utcnow(),
        user_id=user_id,
        company_id=company_id,
        model=model,
        record_id=record_id,
        action=action,
        before_json=before,
        after_json=after,
        ip=ip,
        user_agent=ua,
    )
    db.session.add(entry)
    db.session.flush()
    return entry
