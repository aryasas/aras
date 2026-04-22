# -*- coding: utf-8 -*-
"""
arasCore/lib/audit.py
Lightweight framework audit log.

Writes an aras_audit_log row when:
  - Dynamic app table: AppManagerTable.track_changes = True
  - Code-based model:  class declares __track_changes__ = True

Usage (called automatically via _invoke_hooks in services.py / blueprints.py):
    from arasCore.lib.audit import maybe_log, _snapshot
    maybe_log(obj, action="create", before=None, after=_snapshot(obj))
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# In-process cache: tablename -> bool. Cleared by services.clear_cache().
_track_cache: dict = {}


def _is_tracked(obj) -> bool:
    if getattr(obj.__class__, "__track_changes__", False):
        return True
    tname = getattr(obj, "__tablename__", None)
    if not tname:
        return False
    if tname in _track_cache:
        return _track_cache[tname]
    try:
        from arasCore.arasAdmin.models import AppManagerTable
        tbl = AppManagerTable.query.filter_by(db_table_name=tname).first()
        result = bool(tbl and tbl.track_changes)
    except Exception:
        result = False
    _track_cache[tname] = result
    return result


def invalidate_cache(tablename: str = None):
    """Flush stale track_changes lookups. Called by services.clear_cache()."""
    if tablename:
        _track_cache.pop(tablename, None)
    else:
        _track_cache.clear()


def _snapshot(obj) -> dict | None:
    """Serialize model instance to a plain dict for before/after capture."""
    try:
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
    except Exception:
        return None


def maybe_log(obj, action: str, before: dict = None, after: dict = None):
    """
    Write an ArasCoreAuditLog entry if the model is tracked.
    Safe to call even outside a request context (ip/user_id become None).
    Flushes but does NOT commit — caller's transaction includes it.
    """
    if not _is_tracked(obj):
        return
    try:
        from arasCore.arasAdmin.models import ArasCoreAuditLog
        from arasCore.lib.extensions import db
        user_id = ip = None
        try:
            from flask_login import current_user
            if current_user and current_user.is_authenticated:
                user_id = current_user.id
        except RuntimeError:
            pass
        try:
            from flask import request as _req
            ip = _req.remote_addr
        except RuntimeError:
            pass
        db.session.add(ArasCoreAuditLog(
            ts=datetime.utcnow(),
            user_id=user_id,
            model_name=obj.__tablename__,
            record_id=getattr(obj, "id", None),
            action=action,
            before_json=before,
            after_json=after,
            ip=ip,
        ))
        db.session.flush()
    except Exception as e:
        logger.warning(f"[audit] log failed for {action} on {type(obj).__name__}: {e}")
