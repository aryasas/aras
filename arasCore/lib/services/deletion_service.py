# -*- coding: utf-8 -*-
"""
Framework-level deletion service with backup and restore.

Usage:
    from arasCore.lib.services.deletion_service import execute_deletion, inspect_deletion, execute_restore
"""
import uuid
import logging
from datetime import datetime, date, time
from decimal import Decimal

from arasCore.lib.core.extensions import db
from arasCore.lib.services.linked_doc_detector import detect_linked_docs

logger = logging.getLogger(__name__)

def _json_safe(val):
    if isinstance(val, (datetime, date, time)):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val)
    return val


def _snapshot(obj) -> dict:
    try:
        raw = obj.to_dict() if hasattr(obj, "to_dict") else {
            c.name: getattr(obj, c.name) for c in obj.__table__.columns
        }
        return {k: _json_safe(v) for k, v in raw.items()}
    except Exception:
        return {}


def inspect_deletion(obj) -> dict:
    """Return preview without touching DB. Used by GET /linked-docs/ endpoint."""
    group_id = str(uuid.uuid4())
    nodes    = detect_linked_docs(obj)
    return {
        "group_id": group_id,
        "tree":     [n.as_dict() for n in nodes],
    }


def execute_deletion(obj, user_id=None) -> str:
    """
    1. Detect all linked docs.
    2. Snapshot everything to aras_deleted_doc.
    3. Delete deepest-first.
    4. Single commit.
    Returns group_id string.
    """
    from arasCore.lib.models.deletion_models import DeletedDoc
    from arasCore.lib.services.linked_doc_detector import _resolve_url_info

    group_id = str(uuid.uuid4())
    now      = datetime.utcnow()
    nodes    = detect_linked_docs(obj)  # sorted deepest-first already

    # Also snapshot the root
    root_app, root_res, root_url_prefix = _resolve_url_info(type(obj))
    root_id = getattr(obj, "id", None)
    root_admin_url = f"{root_url_prefix}{root_id}/" if root_url_prefix and root_id else None

    rows_to_delete = []  # (depth, instance)

    def _add_doc(doc_type, doc_id, data, depth, app_slug, resource_slug, admin_url):
        db.session.add(DeletedDoc(
            group_id      = group_id,
            deleted_at    = now,
            deleted_by_id = user_id,
            doc_type      = doc_type,
            doc_id        = doc_id,
            doc_data      = data,
            depth         = depth,
            app_slug      = app_slug,
            resource_slug = resource_slug,
            admin_url     = admin_url,
        ))
        db.session.flush()  # one row at a time to avoid large-packet errors

    # Write backup for root
    _add_doc(type(obj).__name__, root_id, _snapshot(obj), 0,
             root_app, root_res, root_admin_url)
    rows_to_delete.append((0, obj))

    # Write backup for linked docs
    for node in nodes:
        _add_doc(node.doc_type, node.doc_id, _snapshot(node.instance), node.depth,
                 node.app_slug, node.resource_slug, node.admin_url)
        rows_to_delete.append((node.depth, node.instance))

    # Delete deepest-first inside no_autoflush to prevent premature FK violations
    rows_to_delete.sort(key=lambda x: -x[0])
    with db.session.no_autoflush:
        for _, instance in rows_to_delete:
            if hasattr(instance, "before_delete") and callable(instance.before_delete):
                instance.before_delete(user_id=user_id)
            db.session.delete(instance)

    db.session.commit()
    return group_id


def execute_restore(group_id: str, user_id=None) -> None:
    """
    Restore all docs in a deletion group.
    Inserts parent rows first (depth ASC).
    Uses SQLAlchemy models where possible for better safety.
    """
    from arasCore.lib.models.deletion_models import DeletedDoc
    from sqlalchemy import inspect as sa_inspect, text

    docs = (DeletedDoc.query
            .filter_by(group_id=group_id)
            .order_by(DeletedDoc.depth.asc(), DeletedDoc.id.asc())
            .all())

    if not docs:
        raise ValueError(f"No deleted docs found for group_id={group_id}")

    # Collect all SA model classes from mapper registry
    _cls_map: dict = {}
    from arasCore.lib.core.extensions import db
    # We use a broader way to find models if needed, but registry is standard
    from sqlalchemy.orm import declarative_base
    for mapper in db.Model.registry.mappers:
        _cls_map[mapper.class_.__name__] = mapper.class_

    restored_docs = []

    for doc in docs:
        cls = _cls_map.get(doc.doc_type)
        if cls is None:
            logger.warning(f"Restore: Model {doc.doc_type} not found in registry. Skipping.")
            continue

        table = cls.__table__
        pk_val = doc.doc_id

        # Check if PK already exists (could be soft-deleted)
        existing = db.session.execute(
            text(f"SELECT id FROM {table.name} WHERE id = :id"),
            {"id": pk_val}
        ).fetchone()

        if existing:
            if hasattr(cls, "__soft_delete__") and cls.__soft_delete__:
                obj = cls.query.get(pk_val)
                if obj and getattr(obj, "deleted_at", None) is not None:
                    obj.deleted_at = None
                    restored_docs.append(doc)
                    continue
            logger.info(f"Restore: Record {doc.doc_type} #{pk_val} already exists. Skipping.")
            restored_docs.append(doc)
            continue

        # Filter data to only columns that exist in the actual DB table
        db_cols = {row[0] for row in db.session.execute(
            text("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = :t AND TABLE_SCHEMA = DATABASE()"),
            {"t": table.name}
        ).fetchall()}
        data = {k: v for k, v in doc.doc_data.items() if k in db_cols}

        try:
            db.session.execute(table.insert().values(**data))
            restored_docs.append(doc)
        except Exception as e:
            logger.error(f"Restore: Failed to insert {doc.doc_type} #{pk_val}: {e}")
            raise

    # Remove backup rows for successfully restored docs
    for doc in restored_docs:
        db.session.delete(doc)

    db.session.commit()
