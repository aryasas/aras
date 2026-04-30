# -*- coding: utf-8 -*-
"""
Framework-level deletion service with backup and restore.

Usage:
    from arasCore.lib.services.deletion_service import execute_deletion, inspect_deletion, execute_restore
"""
import uuid
from datetime import datetime, date, time
from decimal import Decimal

from arasCore.lib.core.extensions import db
from arasCore.lib.services.linked_doc_detector import detect_linked_docs


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

    # Write backup for root
    db.session.add(DeletedDoc(
        group_id      = group_id,
        deleted_at    = now,
        deleted_by_id = user_id,
        doc_type      = type(obj).__name__,
        doc_id        = root_id,
        doc_data      = _snapshot(obj),
        depth         = 0,
        app_slug      = root_app,
        resource_slug = root_res,
        admin_url     = root_admin_url,
    ))
    rows_to_delete.append((0, obj))

    # Write backup for linked docs (already deepest-first)
    for node in nodes:
        db.session.add(DeletedDoc(
            group_id      = group_id,
            deleted_at    = now,
            deleted_by_id = user_id,
            doc_type      = node.doc_type,
            doc_id        = node.doc_id,
            doc_data      = _snapshot(node.instance),
            depth         = node.depth,
            app_slug      = node.app_slug,
            resource_slug = node.resource_slug,
            admin_url     = node.admin_url,
        ))
        rows_to_delete.append((node.depth, node.instance))

    # Collect StockMovement context before deletion (for valuation recalc after)
    stock_movements_deleted = []
    for _, instance in rows_to_delete:
        cls_name = type(instance).__name__
        if cls_name == "StockMovement":
            for line in getattr(instance, "lines", []):
                stock_movements_deleted.append({
                    "company_id":  instance.company_id,
                    "product_id":  line.product_id,
                    "location_id": instance.src_location_id or instance.dst_location_id,
                })

    # Delete deepest-first
    rows_to_delete.sort(key=lambda x: -x[0])
    for _, instance in rows_to_delete:
        if hasattr(instance, "delete_self") and callable(instance.delete_self):
            instance.delete_self(user_id=user_id)
        else:
            db.session.delete(instance)

    # Flush before recalc so deleted movements are gone from queries
    db.session.flush()

    # Recalculate StockValuation for each affected product/location
    if stock_movements_deleted:
        try:
            from aras.erp.erp_stock.services.posting import recalculate_valuation
            seen = set()
            for info in stock_movements_deleted:
                key = (info["company_id"], info["product_id"], info["location_id"])
                if key not in seen and info["location_id"]:
                    seen.add(key)
                    recalculate_valuation(*key)
        except Exception:
            pass  # ERP not installed or valuation not applicable

    db.session.commit()
    return group_id


def execute_restore(group_id: str, user_id=None) -> None:
    """
    Restore all docs in a deletion group.
    Inserts parent rows first (depth ASC), skips if PK already exists.
    Removes DeletedDoc rows on success.
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
    for m in sa_inspect(DeletedDoc).mapper.registry.mappers:
        _cls_map[m.class_.__name__] = m.class_

    restored = []
    for doc in docs:
        cls = _cls_map.get(doc.doc_type)
        if cls is None:
            continue  # unknown model, skip

        table = cls.__table__
        pk_val = doc.doc_id

        # Check if PK already exists
        existing = db.session.execute(
            text(f"SELECT id FROM {table.name} WHERE id = :id"),
            {"id": pk_val}
        ).fetchone()
        if existing:
            continue  # already recreated, skip

        # Filter data to only known columns
        col_names = {c.name for c in table.columns}
        data = {k: v for k, v in doc.doc_data.items() if k in col_names}

        db.session.execute(table.insert().values(**data))
        restored.append(doc)

    # Remove backup rows for successfully restored docs
    for doc in restored:
        db.session.delete(doc)

    db.session.commit()
