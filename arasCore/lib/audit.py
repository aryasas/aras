# -*- coding: utf-8 -*-
"""
arasCore/lib/audit.py
Lightweight framework audit log + field-level change versioning.

Writes an aras_audit_log row (row-level) and/or audit_field_log rows
(field-level) when:
  - Dynamic app table: AppManagerTable.track_changes = True
  - Code-based model:  class declares __track_changes__ = True
  - Field-level opt-in: class declares __audit_fields__ = True

Usage:
    from arasCore.lib.audit import maybe_log, record_field_diff, _snapshot
    maybe_log(obj, action="update", before=before_snap, after=_snapshot(obj))
    record_field_diff(obj, before_snap, _snapshot(obj))
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


def _get_user_and_ip():
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
    return user_id, ip


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
        user_id, ip = _get_user_and_ip()
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


def record_field_diff(obj, before: dict | None, after: dict | None):
    """
    Write one AuditFieldLog row per changed field.
    Opt-in via model.__audit_fields__ = True or AppManagerTable.track_changes = True.
    """
    if not _is_tracked(obj):
        return
    if not before or not after:
        return
    changed = {k: (before.get(k), after.get(k))
               for k in after if str(before.get(k)) != str(after.get(k))}
    if not changed:
        return
    try:
        from arasCore.lib.audit_models import AuditFieldLog
        from arasCore.lib.extensions import db
        user_id, _ = _get_user_and_ip()
        tname = obj.__tablename__
        rec_id = getattr(obj, "id", None)
        app_slug = tname.split("_")[0] if "_" in tname else tname
        now = datetime.utcnow()
        for fname, (old_val, new_val) in changed.items():
            db.session.add(AuditFieldLog(
                app=app_slug,
                resource=tname,
                object_id=rec_id,
                field_name=fname,
                old_value=str(old_val) if old_val is not None else None,
                new_value=str(new_val) if new_val is not None else None,
                changed_by_id=user_id,
                changed_at=now,
            ))
        db.session.flush()
    except Exception as e:
        logger.warning(f"[audit] field_diff failed on {type(obj).__name__}: {e}")
