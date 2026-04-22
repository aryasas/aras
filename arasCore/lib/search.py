# -*- coding: utf-8 -*-
"""
arasCore/lib/search.py
=======================
Global search across all registered resources whose columns are marked
searchable=True (AppManagerColumn) or whose ResourceDef.searchable is set.

Public API:
  global_search(q, user, max_per_resource=5) → list of result dicts

Result dict:
  {
    "app":   str,
    "resource": str,
    "title": str,
    "url":   str,   # admin edit URL
    "match": str,   # snippet
  }

Mounted by api_handler at GET /api/_search/?q=foo
"""
import logging

logger = logging.getLogger(__name__)


def global_search(q: str, user=None, max_per_resource: int = 5) -> list:
    if not q or len(q.strip()) < 2:
        return []
    q = q.strip()
    results = []

    # ── 1. Dynamic apps (DB-based) ────────────────────────────────────────────
    try:
        results.extend(_search_dynamic_apps(q, user, max_per_resource))
    except Exception as e:
        logger.warning(f"[search] dynamic search error: {e}")

    # ── 2. Code-based apps (manifest) ─────────────────────────────────────────
    try:
        results.extend(_search_manifest_apps(q, user, max_per_resource))
    except Exception as e:
        logger.warning(f"[search] manifest search error: {e}")

    return results


def _search_dynamic_apps(q, user, max_per_resource):
    from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable, AppManagerColumn
    from arasCore.arasAdmin.services import make_table_model
    from arasCore.lib.extensions import db

    results = []
    apps = AppManagerApp.query.filter_by(is_active=True).all()

    for app in apps:
        tables = AppManagerTable.query.filter_by(app_id=app.id, is_active=True).all()
        for tbl in tables:
            search_cols = [
                c.name for c in AppManagerColumn.query.filter_by(
                    table_id=tbl.id, searchable=True
                ).all()
            ]
            if not search_cols:
                continue

            try:
                model = make_table_model(tbl, app.name, tables)
                import sqlalchemy as _sa
                conditions = [
                    getattr(model, col).ilike(f"%{q}%")
                    for col in search_cols
                    if hasattr(model, col)
                ]
                if not conditions:
                    continue
                rows = model.query.filter(_sa.or_(*conditions)).limit(max_per_resource).all()
                adm_url = f"/admin{tbl.get_full_url(app.url)}"
                for row in rows:
                    match_val = _extract_match(row, search_cols, q)
                    results.append({
                        "app":      app.title,
                        "resource": tbl.get_menu_title(),
                        "title":    _row_label(row),
                        "url":      f"{adm_url}/{row.id}/",
                        "match":    match_val,
                    })
            except Exception as e:
                logger.debug(f"[search] table {tbl.name}: {e}")

    return results


def _search_manifest_apps(q, user, max_per_resource):
    from arasCore.lib.blueprints import get_helper_registry
    from arasCore.lib.extensions import db

    results = []
    for helper in get_helper_registry().values():
        for res in helper.resources:
            if not res.model:
                continue
            searchable = getattr(res, "searchable", []) or []
            if not searchable:
                continue
            try:
                import sqlalchemy as _sa
                model = res.model
                conditions = [
                    getattr(model, col).ilike(f"%{q}%")
                    for col in searchable
                    if hasattr(model, col)
                ]
                if not conditions:
                    continue
                rows = model.query.filter(_sa.or_(*conditions)).limit(max_per_resource).all()
                adm_url = f"/admin/{helper.admin_slug or helper.name}/{res.name}"
                for row in rows:
                    match_val = _extract_match(row, searchable, q)
                    results.append({
                        "app":      helper.title,
                        "resource": res.get_menu_title(),
                        "title":    _row_label(row),
                        "url":      f"{adm_url}/{row.id}/",
                        "match":    match_val,
                    })
            except Exception as e:
                logger.debug(f"[search] manifest {helper.name}/{res.name}: {e}")

    return results


def _row_label(row) -> str:
    for attr in ("name", "title", "username", "email", "label", "subject"):
        v = getattr(row, attr, None)
        if v:
            return str(v)
    return f"#{row.id}"


def _extract_match(row, search_cols, q) -> str:
    for col in search_cols:
        v = getattr(row, col, None)
        if v and q.lower() in str(v).lower():
            text = str(v)
            idx  = text.lower().index(q.lower())
            start = max(0, idx - 20)
            end   = min(len(text), idx + len(q) + 20)
            return ("…" if start > 0 else "") + text[start:end] + ("…" if end < len(text) else "")
    return ""
