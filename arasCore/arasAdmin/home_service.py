# -*- coding: utf-8 -*-
"""
arasCore/arasAdmin/home_service.py
==================================
Standard home page for each app — `/admin/<app>/`.

Renders:
  - App header (title, icon, description)
  - Dashboard widgets (from mgr_dashboard + inline defaults)
  - Page-type grid (tables where show_in_home=true)

Auto-mounted for both code-based apps (via blueprints._register_helper) and
dynamic apps (via services._register_built_app).
"""
import logging
from flask import render_template
from flask_login import login_required

logger = logging.getLogger(__name__)


# ── Widget registry ──────────────────────────────────────────────────────────
#
# Key → callable(app_row, widget_row) -> dict with at least {"value"}.
# Apps can register more via `register_widget_source()`.
_WIDGET_SOURCES: dict = {}


def register_widget_source(key: str, fn):
    """Register a widget data-source function by key."""
    _WIDGET_SOURCES[key] = fn


def _resolve_widget(widget_row, app_row):
    """Return dict {value, label, icon, color, link, width, type, extra} for UI."""
    src = widget_row.data_source or ""
    extra = {}

    # Built-in: "model:<ab_app_table>" → row count
    if src.startswith("model:"):
        table_name = src.split(":", 1)[1].strip()
        value = _count_rows(table_name)
    elif src in _WIDGET_SOURCES:
        try:
            res = _WIDGET_SOURCES[src](app_row, widget_row)
            if isinstance(res, dict):
                value = res.get("value")
                extra = {k: v for k, v in res.items() if k != "value"}
            else:
                value = res
        except Exception as e:
            logger.warning(f"[home] widget '{widget_row.name}' failed: {e}")
            value = "—"
    else:
        value = "—"

    return {
        "name":  widget_row.name,
        "label": widget_row.label,
        "value": value,
        "icon":  widget_row.icon or "fa-chart-bar",
        "color": widget_row.color or "primary",
        "link":  widget_row.link_url,
        "width": widget_row.width or 3,
        "type":  widget_row.widget_type or "count",
        "extra": extra,
    }


def _count_rows(db_table_name: str):
    from arasCore.lib.extensions import db
    from sqlalchemy import text
    try:
        result = db.session.execute(text(f"SELECT COUNT(*) FROM `{db_table_name}`")).scalar()
        return int(result or 0)
    except Exception:
        return 0


# ── Home view ────────────────────────────────────────────────────────────────

def _get_app_record(app_name: str):
    """Resolve app metadata. Falls back to code-based AppHelper registry."""
    from arasCore.arasAdmin.models import AppManagerApp
    return AppManagerApp.query.filter_by(name=app_name).first()


def _get_page_tiles(app_name: str):
    """Tiles for /admin/<app>/ grid — tables with show_in_home=true (dynamic apps
    only). Returns [{title, icon, url, description, page_type, count}]."""
    from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable
    app_row = AppManagerApp.query.filter_by(name=app_name).first()
    if not app_row:
        return []
    tiles = []
    rows = (
        AppManagerTable.query
        .filter_by(app_id=app_row.id, is_active=True)
        .order_by(AppManagerTable.menu_order)
        .all()
    )
    for t in rows:
        show = getattr(t, "show_in_home", True)
        if show is False:
            continue
        tiles.append({
            "title":       t.get_menu_title(),
            "icon":        t.icon or t.menu_icon or "fa-table",
            "url":         f"/admin{t.get_full_url(app_row.url)}/",
            "description": getattr(t, "description", None) or "",
            "page_type":   getattr(t, "page_type", "list") or "list",
            "count":       _count_rows(t.get_db_table_name(app_name)),
        })
    return tiles


def _get_helper_tiles(app_name: str):
    """Tiles for code-based app (from AppHelper resources/menu_groups)."""
    try:
        from arasCore.lib.blueprints import get_helper_registry
    except Exception:
        return []

    helper = get_helper_registry().get(app_name)
    if not helper:
        return []

    tiles = []
    if helper.menu_groups:
        for grp in sorted(helper.menu_groups, key=lambda g: g.order):
            grp_resources = [r for r in grp.resources if r.admin_list]
            if not grp_resources:
                continue
            # Each group shown as a single tile linking to the group sub-page
            grp_slug = grp.title.lower().replace(" ", "-")
            tiles.append({
                "title":       grp.title,
                "icon":        grp.icon or "fa-folder",
                "url":         f"/admin/{app_name}/{grp_slug}/",
                "description": f"{len(grp_resources)} menu{'s' if len(grp_resources) != 1 else ''}",
                "page_type":   "group",
                "count":       None,
                "group":       None,
            })
    else:
        for res in helper.resources:
            if not res.admin_list:
                continue
            tiles.append({
                "title":       res.get_menu_title(),
                "icon":        res.menu_icon or "fa-table",
                "url":         f"/admin/{app_name}/{res.name}/",
                "description": "",
                "page_type":   "list",
                "count":       None,
                "group":       None,
            })
    return tiles


def _get_dashboard_widgets(app_row):
    """Resolved widgets for this app."""
    if not app_row:
        return []
    from arasCore.arasAdmin.models import AppManagerDashboard
    rows = (
        AppManagerDashboard.query
        .filter_by(app_id=app_row.id, is_active=True)
        .order_by(AppManagerDashboard.order)
        .all()
    )
    return [_resolve_widget(w, app_row) for w in rows]


def make_home_view(app_name: str, app_title: str, is_dynamic: bool = False):
    """Factory for `/admin/<app_name>/` view function."""
    @login_required
    def view():
        app_row = _get_app_record(app_name)

        # Tiles: dynamic apps from AppManagerTable, code-based from AppHelper
        tiles = _get_page_tiles(app_name) if is_dynamic else _get_helper_tiles(app_name)

        widgets = _get_dashboard_widgets(app_row)

        # Description & icon
        description = (app_row.description if app_row else "") or ""
        icon        = (app_row.icon if app_row else None) or "fa-cubes"

        return render_template(
            "admin/adm_app_home.html",
            title=app_title,
            main_title=app_title,
            app_name=app_name,
            app_title=app_title,
            app_description=description,
            app_icon=icon,
            app_url=(app_row.url if app_row else f"/{app_name}"),
            tiles=tiles,
            widgets=widgets,
            is_dynamic=is_dynamic,
            settings_url=f"/admin/{app_name}/settings/",
        )
    return view


def mount_home_route(flask_app_or_bp, app_name: str, app_title: str,
                     is_dynamic: bool = False, endpoint: str = None):
    """Register `/admin/<app_name>/` home page."""
    url = f"/admin/{app_name}/"
    ep  = endpoint or f"home_{app_name}"
    try:
        view = make_home_view(app_name, app_title, is_dynamic=is_dynamic)
        flask_app_or_bp.add_url_rule(url, endpoint=ep, view_func=view, methods=["GET"])
        logger.debug(f"[home] mounted {url} (ep={ep})")
    except AssertionError:
        logger.debug(f"[home] {ep} already registered; skip")
    except Exception as e:
        logger.warning(f"[home] mount failed for {url}: {e}")


# ── Group home ────────────────────────────────────────────────────────────────

def make_group_view(app_name: str, app_title: str):
    """
    Factory for `/admin/<app_name>/<group_slug>/`.
    Renders tiles for all resources in that MenuGroup.
    """
    from arasCore.lib.blueprints import get_helper_registry

    @login_required
    def view(group_slug: str):
        helper = get_helper_registry().get(app_name)
        if not helper:
            from flask import abort
            abort(404)

        # Find the matching group by slug
        target_group = None
        for grp in (helper.menu_groups or []):
            slug = grp.title.lower().replace(" ", "-")
            if slug == group_slug:
                target_group = grp
                break

        if not target_group:
            from flask import abort
            abort(404)

        tiles = [
            {
                "title":       res.get_menu_title(),
                "icon":        res.menu_icon or "fa-table",
                "url":         f"/admin/{app_name}/{res.name}/",
                "description": "",
                "page_type":   "list",
                "count":       None,
                "group":       None,
            }
            for res in target_group.resources if res.admin_list
        ]

        return render_template(
            "admin/adm_group_home.html",
            title=f"{target_group.title} — {app_title}",
            main_title=app_title,
            app_name=app_name,
            app_title=app_title,
            group_title=target_group.title,
            group_icon=target_group.icon,
            tiles=tiles,
            back_url=f"/admin/{app_name}/",
        )
    return view


def mount_group_route(flask_app_or_bp, app_name: str, app_title: str,
                      endpoint: str = None):
    """Register `/admin/<app_name>/<group_slug>/` for MenuGroup sub-pages."""
    url = f"/admin/{app_name}/<group_slug>/"
    ep  = endpoint or f"group_{app_name}"
    try:
        view = make_group_view(app_name, app_title)
        flask_app_or_bp.add_url_rule(url, endpoint=ep, view_func=view, methods=["GET"])
        logger.debug(f"[home] mounted group route {url} (ep={ep})")
    except AssertionError:
        logger.debug(f"[home] {ep} already registered; skip")
    except Exception as e:
        logger.warning(f"[home] group mount failed for {url}: {e}")
