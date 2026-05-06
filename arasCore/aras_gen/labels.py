"""Single-source label resolver — DB (mgr_column.label) wins over code, code wins over humanized name.

Code-declared `Col(label=...)` is the *default*; once registered it is mirrored into
mgr_column so the GUI can edit it. From then on, mgr_column is the authoritative source.
"""
from __future__ import annotations
from flask import g, has_app_context, has_request_context
import logging

logger = logging.getLogger(__name__)


def _humanize(name: str) -> str:
    return name.replace("_", " ").title() if name else ""


def _cache():
    """Per-request cache of (table, name) -> resolved label, to avoid N queries per page."""
    if has_request_context():
        c = getattr(g, "_aras_label_cache", None)
        if c is None:
            c = {}
            g._aras_label_cache = c
        return c
    return None


def resolve_label(table: str, name: str, code_label: str | None) -> str:
    fallback = code_label or _humanize(name)
    if not table or not name or not has_app_context():
        return fallback

    cache = _cache()
    key = (table, name)
    if cache is not None and key in cache:
        return cache[key]

    try:
        from arasCore.admin.models import AppManagerColumn, AppManagerTable
        from arasCore.lib.core.base_model import db
        row = (
            db.session.query(AppManagerColumn.label)
            .join(AppManagerTable, AppManagerColumn.table_id == AppManagerTable.id)
            .filter(AppManagerTable.name == table, AppManagerColumn.name == name)
            .first()
        )
        if row and row[0]:
            label = row[0]
        else:
            label = fallback
            _seed_mgr_column(table, name, label)
    except Exception as e:
        logger.debug(f"[label] resolve fail {table}.{name}: {e}")
        label = fallback

    if cache is not None:
        cache[key] = label
    return label


def _seed_mgr_column(table: str, name: str, label: str) -> None:
    """Best-effort seed: create the mgr_column row so the GUI has something to edit.
    Silently no-op if mgr_table row is missing or DB is read-only / not yet migrated.
    """
    try:
        from arasCore.admin.models import AppManagerColumn, AppManagerTable
        from arasCore.lib.core.base_model import db
        tbl = db.session.query(AppManagerTable).filter_by(name=table).first()
        if not tbl:
            return
        exists = db.session.query(AppManagerColumn.id).filter_by(table_id=tbl.id, name=name).first()
        if exists:
            return
        db.session.add(AppManagerColumn(table_id=tbl.id, name=name, label=label, field_type="string"))
        db.session.commit()
    except Exception:
        try:
            from arasCore.lib.core.base_model import db
            db.session.rollback()
        except Exception:
            pass
