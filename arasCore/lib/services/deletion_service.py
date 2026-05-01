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
            # For StockMovement, we need product_id and location_id
            # Lines might have product_id
            product_id = getattr(instance, "product_id", None)
            location_id = instance.src_location_id or instance.dst_location_id
            if not product_id and hasattr(instance, "lines"):
                for line in instance.lines:
                    stock_movements_deleted.append({
                        "company_id":  instance.company_id,
                        "product_id":  line.product_id,
                        "location_id": location_id,
                    })
            elif product_id:
                stock_movements_deleted.append({
                    "company_id":  instance.company_id,
                    "product_id":  product_id,
                    "location_id": location_id,
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
                if key not in seen and info["location_id"] and info["product_id"]:
                    seen.add(key)
                    recalculate_valuation(*key)
        except Exception as e:
            logger.error(f"Error recalculating valuation: {e}")

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
    affected_valuation_keys = []

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
            # If soft-delete model, restore by clearing deleted_at
            if hasattr(cls, "__soft_delete__") and cls.__soft_delete__:
                # Use query.get() bypasses _q() soft-delete filter
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

        # Use raw insert to preserve ID
        try:
            db.session.execute(table.insert().values(**data))
            
            # Queue valuation recalc from StockMovementLine (product lives on the line)
            if doc.doc_type == "StockMovementLine":
                mv_doc = next((d for d in docs if d.doc_type == "StockMovement"
                               and d.doc_id == data.get("movement_id")), None)
                mv_data = mv_doc.doc_data if mv_doc else {}
                affected_valuation_keys.append({
                    "company_id": mv_data.get("company_id"),
                    "product_id": data.get("product_id"),
                    "location_id": mv_data.get("src_location_id") or mv_data.get("dst_location_id"),
                })
            
            restored_docs.append(doc)
        except Exception as e:
            logger.error(f"Restore: Failed to insert {doc.doc_type} #{pk_val}: {e}")
            raise

    # Trigger valuation recalc for restored movements
    if affected_valuation_keys:
        try:
            from aras.erp.erp_stock.services.posting import recalculate_valuation
            seen = set()
            for info in affected_valuation_keys:
                key = (info["company_id"], info["product_id"], info["location_id"])
                if key not in seen and all(key):
                    seen.add(key)
                    recalculate_valuation(*key)
        except Exception:
            pass

    # Remove backup rows for successfully restored docs
    for doc in restored_docs:
        db.session.delete(doc)

    db.session.commit()
