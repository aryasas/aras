# -*- coding: utf-8 -*-
"""Sidebar menu builder with RBAC filtering."""
import logging

logger = logging.getLogger(__name__)


def _slug_from_url(url: str) -> str:
    return url.strip("/") or "app"


def _build_raw_menu() -> list:
    """Build raw sidebar menu tree entirely from DB (no RBAC filter)."""
    from arasCore.admin.models import AppManagerApp, AppManagerTable

    def _node_to_dict(t, app_url):
        return {
            "title":    t.get_menu_title(),
            "icon":     t.menu_icon or "fa-table",
            "url":      f"/admin{t.get_full_url(app_url)}/",
            "children": [],
        }

    result = []
    try:
        apps = AppManagerApp.query.filter_by(is_active=True).order_by(AppManagerApp.menu_order).all()
        for app in apps:
            tables = (
                AppManagerTable.query
                .filter_by(app_id=app.id, show_in_menu=True)
                .order_by(AppManagerTable.menu_order)
                .all()
            )
            app_url = app.url_prefix
            tbl_map = {t.id: {"tbl": t, "node": _node_to_dict(t, app_url)} for t in tables}
            roots = []
            for t in tables:
                entry = tbl_map[t.id]
                if t.parent_table_id and t.parent_table_id in tbl_map:
                    tbl_map[t.parent_table_id]["node"]["children"].append(entry["node"])
                else:
                    roots.append(entry["node"])

            adm_slug = _slug_from_url(app_url)
            result.append({
                "title":    app.title,
                "icon":     app.icon or "fa-cubes",
                "order":    app.menu_order or 99,
                "url":      f"/admin/{adm_slug}/",
                "children": list(roots),
                "source":   "db",
                "app_slug": adm_slug,
            })
    except Exception as e:
        logger.warning(f"[menu_service] menu build error: {e}")

    # Static framework entries
    result.append({
        "title":    "Trash",
        "icon":     "fa-trash-o",
        "order":    999,
        "url":      "/admin/trash/",
        "children": [],
        "source":   "framework",
        "app_slug": "trash",
    })

    return sorted(result, key=lambda x: x.get("order", 99))


def build_sidebar_menu() -> list:
    """Return sidebar menu tree, filtered by RBAC. Raw tree cached 60 s."""
    try:
        from arasCore.lib.core.extensions import cache as _cache
        raw = _cache.get("_sidebar_raw")
        if raw is None:
            raw = _build_raw_menu()
            _cache.set("_sidebar_raw", raw, timeout=60)
    except Exception:
        raw = _build_raw_menu()

    try:
        from flask_login import current_user
        if current_user.is_authenticated:
            return _filter_menu_for_user(raw, current_user)
    except Exception:
        pass
    return raw


def _filter_menu_for_user(menu_items, user):
    """Remove apps/pages the user has no 'view' permission for."""
    from arasCore.rbac import get_user_allowed_resources

    filtered = []
    for item in menu_items:
        app_slug = item.get("name") or item.get("app_slug")
        if not app_slug:
            url = item.get("url", "")
            parts = url.strip("/").split("/")
            app_slug = parts[1] if len(parts) >= 2 and parts[0] == "admin" else None

        if not app_slug:
            filtered.append(item)
            continue

        allowed = get_user_allowed_resources(user, app_slug)
        if allowed is None:
            filtered.append(item)
            continue

        children = item.get("children", [])
        visible_children = []
        for child in children:
            child_url = child.get("url", "")
            c_parts = child_url.strip("/").split("/")
            res_slug = "/".join(c_parts[2:]) if len(c_parts) >= 3 else None
            if res_slug is None or res_slug in allowed:
                visible_children.append(child)
            elif child.get("children"):
                sub_children = [
                    sc for sc in child["children"]
                    if (lambda u: "/".join(u.strip("/").split("/")[2:]) or None)(sc.get("url", "")) in allowed
                ]
                if sub_children:
                    visible_children.append({**child, "children": sub_children})

        if visible_children:
            filtered.append({**item, "children": visible_children})
        elif allowed:
            filtered.append({**item, "children": []})

    return filtered
