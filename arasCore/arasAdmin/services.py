# -*- coding: utf-8 -*-
"""
arasCore/arasAdmin/services.py
Re-exports from split modules for backward compatibility.
Logic lives in: column_factory, table_registry, menu_service, crud_factory.
"""
import logging
from flask import Blueprint

from arasCore.lib.extensions import db
from arasCore.lib.label_utils import humanize as _humanize_label, row_display, find_ref_model as _find_ref_model

logger = logging.getLogger(__name__)

_SYSTEM_COLS = {"id", "created_at", "updated_at", "deleted_at",
                "created_by", "updated_by", "created_by_id", "updated_by_id"}


def _slug_from_url(url: str) -> str:
    return url.strip("/") or "app"


# ── column_factory ────────────────────────────────────────────────────────────
from arasCore.arasAdmin.column_factory import _make_sa_column, _make_wtf_field  # noqa: E402

# ── table_registry ────────────────────────────────────────────────────────────
from arasCore.arasAdmin.table_registry import (  # noqa: E402
    _table_registry,
    apply_search_and_filters,
    sync_table_columns,
    clear_cache,
    make_table_model,
    make_table_form,
    get_view_columns,
)

# ── menu_service ──────────────────────────────────────────────────────────────
from arasCore.arasAdmin.menu_service import (  # noqa: E402
    _build_raw_menu,
    build_sidebar_menu,
    _filter_menu_for_user,
)

# ── crud_factory ──────────────────────────────────────────────────────────────
from arasCore.arasAdmin.crud_factory import (  # noqa: E402
    _invoke_hooks,
    _load_activity_log,
    _populate_relation_choices,
    _detect_parent_fk,
    _get_child_tables_for_model,
    _get_inline_columns,
    make_adm_list,
    make_adm_add,
    make_adm_edit,
    make_adm_delete,
    make_adm_bulk_delete,
    make_web_list,
    make_web_add,
    make_web_edit,
    make_web_delete,
)


# ── _register_built_app ───────────────────────────────────────────────────────

def _register_built_app(app_def_id, flask_app):
    """Register one AppManagerApp (all its tables) as a single Flask blueprint."""
    with flask_app.app_context():
        try:
            from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable
            app_def = AppManagerApp.query.get(app_def_id)
            if not app_def:
                logger.warning(f"[services] app_def id={app_def_id} not found.")
                return False

            all_tbls = app_def.get_tables()
            ordered, seen = [], set()

            def _visit(t):
                if t.id in seen:
                    return
                if t.parent_table_id:
                    parent = next((x for x in all_tbls if x.id == t.parent_table_id), None)
                    if parent:
                        _visit(parent)
                seen.add(t.id)
                ordered.append(t)

            for t in all_tbls:
                _visit(t)

            table_models = {}
            for tbl in ordered:
                model = make_table_model(tbl, app_def.slug, all_tbls)
                model.__table__.create(db.engine, checkfirst=True)
                sync_table_columns(model)
                table_models[tbl.id] = model

            app_name       = app_def.slug
            app_url        = app_def.url_prefix
            app_main_title = app_def.title
            admin_slug     = _slug_from_url(app_url)

            table_snapshots = []
            for tbl in ordered:
                if not tbl.is_active:
                    continue
                form_cls  = make_table_form(tbl, table_models[tbl.id], app_def.id)
                vcols     = get_view_columns(tbl)
                full_url  = tbl.get_full_url(app_url)
                menu_tit  = tbl.get_menu_title()
                tbl_name  = tbl.name
                table_snapshots.append({
                    "name":               tbl_name,
                    "title":              tbl.title,
                    "menu_title":         menu_tit,
                    "url":                full_url,
                    "model":              table_models[tbl.id],
                    "form":               form_cls,
                    "vcols":              vcols,
                    "app_title":          app_def.title,
                    "app_id":             app_def.id,
                    "table_id":           tbl.id,
                    "parent_table_id":    tbl.parent_table_id,
                    "app_slug":           admin_slug,
                    "required_role_slug": tbl.required_role_slug,
                    "per_page":           tbl.per_page or 20,
                    "layout_json":        tbl.layout_json if hasattr(tbl, "layout_json") else None,
                })

        except Exception as e:
            logger.error(f"[services] Error loading app_def id={app_def_id}: {e}", exc_info=True)
            return False

    try:
        bp_safe = f"mgr_{admin_slug.replace('-', '_')}"

        stale_bp_prefixes = {
            bp_key + "."
            for bp_key in list(flask_app.blueprints.keys())
            if bp_key == bp_safe or bp_key.startswith(bp_safe + "_")
        }
        for bp_key in list(flask_app.blueprints.keys()):
            if bp_key == bp_safe or bp_key.startswith(bp_safe + "_"):
                flask_app.blueprints.pop(bp_key)

        stale_rules = [
            r for r in flask_app.url_map._rules
            if any(r.endpoint.startswith(pfx) for pfx in stale_bp_prefixes)
        ]
        if stale_rules:
            for rule in stale_rules:
                flask_app.url_map._rules.remove(rule)
                flask_app.url_map._rules_by_endpoint.pop(rule.endpoint, None)
                flask_app.view_functions.pop(rule.endpoint, None)
            flask_app.url_map.update()
            logger.info(f"[services] Purged {len(stale_rules)} stale route(s) for '{admin_slug}'.")

        bp_name = bp_safe if bp_safe not in flask_app.blueprints else f"{bp_safe}_{__import__('time').time_ns()}"
        bp = Blueprint(bp_name, __name__)

        for snap in table_snapshots:
            _register_table_routes(bp, snap, table_snapshots)

        try:
            from arasCore.arasAdmin.settings_service import mount_settings_route
            mount_settings_route(
                bp, admin_slug, app_main_title,
                schema=[], is_dynamic=True,
                endpoint=f"settings_{admin_slug}",
                registry_key=app_name,
            )
        except Exception as _se:
            logger.warning(f"[services] settings mount failed for {admin_slug}: {_se}")

        try:
            from arasCore.arasAdmin.home_service import mount_home_route
            mount_home_route(
                bp, admin_slug, app_main_title,
                is_dynamic=True,
                endpoint=f"home_{admin_slug}",
                registry_key=app_name,
            )
        except Exception as _he:
            logger.warning(f"[services] home mount failed for {admin_slug}: {_he}")

        if table_snapshots:
            first_url = table_snapshots[0]["url"] + "/"

            def make_app_index(target=first_url):
                from flask import redirect as _redir
                def view():
                    return _redir(target)
                return view

            try:
                bp.add_url_rule(
                    f"{app_url}/",
                    endpoint=f"{app_name}_pub_index",
                    view_func=make_app_index(),
                )
            except Exception as _ie:
                logger.debug(f"[services] pub index already registered for {app_name}: {_ie}")

        flask_app.register_blueprint(bp)
        logger.info(f"[services] Registered app '{app_name}' with {len(table_snapshots)} table(s).")
        return True

    except Exception as e:
        logger.error(f"[services] Failed to register {app_name}: {e}", exc_info=True)
        return False


def _register_table_routes(bp, snap, all_snaps):
    """Add CRUD + API routes for one table into blueprint bp."""
    model     = snap["model"]
    form_cls  = snap["form"]
    title     = snap["title"]
    main_t    = snap["menu_title"]
    burl      = snap["url"]
    tname     = snap["name"]
    vcols     = snap["vcols"]
    app_title = snap["app_title"]
    app_id    = snap["app_id"]
    table_id  = snap["table_id"]
    app_slug    = snap.get("app_slug", "")
    req_role    = snap.get("required_role_slug")
    layout_json = snap.get("layout_json")
    sibling_tabs = [(s["title"], s["url"]) for s in all_snaps]

    cur_table_id = snap.get("table_id")
    child_snaps = [
        s for s in all_snaps
        if s.get("parent_table_id") and s["parent_table_id"] == cur_table_id
    ]
    child_defs = []
    for cs in child_snaps:
        fk_col = _detect_parent_fk(cs["model"], model)
        if fk_col:
            from arasCore.lib.api_handler import get_api_url_for_model
            child_defs.append({
                "title":          cs["title"],
                "model":          cs["model"],
                "vcols":          cs["vcols"],
                "adm_url":        f"/admin{cs['url']}",
                "fk_col":         fk_col,
                "api_url":        get_api_url_for_model(cs["model"]),
                "inline_columns": _get_inline_columns(cs["model"], fk_col),
            })

    ep      = tname
    adm_url = f"/admin{burl}"

    bp.add_url_rule(f"{burl}/",               endpoint=f"{ep}_index",      view_func=make_web_list(model, title, main_t, vcols, burl, app_title, app_id, table_id, sibling_tabs, burl))
    bp.add_url_rule(f"{burl}/add/",           endpoint=f"{ep}_add",        view_func=make_web_add(model, form_cls, title, main_t, burl, app_title, app_id, table_id, sibling_tabs, burl),  methods=["GET","POST"])
    bp.add_url_rule(f"{burl}/<int:item_id>/", endpoint=f"{ep}_edit",       view_func=make_web_edit(model, form_cls, title, main_t, burl, app_title, app_id, table_id, sibling_tabs, burl), methods=["GET","POST"])
    bp.add_url_rule(f"{burl}/<int:item_id>/delete/", endpoint=f"{ep}_delete", view_func=make_web_delete(model, burl), methods=["POST"])

    bp.add_url_rule(f"{adm_url}/",               endpoint=f"{ep}_adm_index",       view_func=make_adm_list(model, title, main_t, vcols, adm_url, app_title, app_id, table_id, sibling_tabs, adm_url, app_slug, req_role, tname, apply_search_and_filters, layout_json=layout_json, per_page=snap.get("per_page", 20)))
    bp.add_url_rule(f"{adm_url}/add/",           endpoint=f"{ep}_adm_add",         view_func=make_adm_add(model, form_cls, title, main_t, adm_url, app_title, app_id, table_id, sibling_tabs, adm_url, app_slug, req_role, tname, layout_json=layout_json),  methods=["GET","POST"])
    bp.add_url_rule(f"{adm_url}/<int:item_id>/", endpoint=f"{ep}_adm_edit",        view_func=make_adm_edit(model, form_cls, title, main_t, adm_url, app_title, app_id, table_id, sibling_tabs, adm_url, app_slug, req_role, tname, layout_json=layout_json, child_defs=child_defs), methods=["GET","POST"])
    bp.add_url_rule(f"{adm_url}/<int:item_id>/delete/", endpoint=f"{ep}_adm_delete", view_func=make_adm_delete(model, adm_url, app_slug, req_role, tname), methods=["POST"])
    bp.add_url_rule(f"{adm_url}/bulk-delete/",   endpoint=f"{ep}_adm_bulk_delete", view_func=make_adm_bulk_delete(model, adm_url, app_slug, req_role, tname), methods=["POST"])

    try:
        from arasCore.lib.api_handler import register_api_model
        register_api_model(burl.strip("/"), model)
    except Exception as _e:
        logger.warning(f"[services] api_handler register skipped: {_e}")


# ── load_all_built_apps ───────────────────────────────────────────────────────

def load_all_built_apps(flask_app):
    """Load all active AppManagerApp records and register them as blueprints."""
    try:
        from arasCore.arasAdmin.models import AppManagerApp
        from arasCore.lib.blueprints import get_helper_registry
        with flask_app.app_context():
            db.create_all()
            apps = AppManagerApp.query.filter_by(is_active=True).all()
            app_ids = [(a.id, a.slug) for a in apps]
            logger.info(f"[services] Found {len(app_ids)} active built app(s).")

        helper_registry = get_helper_registry()
        for app_id, app_name in app_ids:
            if app_name in helper_registry:
                logger.info(f"[services] skip '{app_name}' — already handled by Python manifest")
                continue
            _register_built_app(app_id, flask_app)

    except Exception as e:
        logger.warning(f"[services] Could not load built apps: {e}")


# ── Dashboard Widgets ─────────────────────────────────────────────────────────

def get_dashboard_widgets(user, app_id: int = None):
    """
    Return list of widget dicts for the admin dashboard.
    When app_id is provided, returns DB-driven widgets for that app
    filtered by user/role scope. Falls back to built-in system widgets.
    """
    from arasCore.auth import User
    from arasCore.permissions import UserRole

    widgets = []

    # DB-driven widgets (app-specific or global via app_id)
    if app_id is not None:
        try:
            from arasCore.arasAdmin.models import AppManagerDashboard
            from arasCore.lib.widget_registry import resolve_widget
            from sqlalchemy import or_

            # Collect user's role IDs
            user_role_ids = [
                r.role_id for r in UserRole.query.filter_by(user_id=user.id).all()
            ] if user.is_authenticated else []

            q = AppManagerDashboard.query.filter_by(app_id=app_id, is_active=True)
            q = q.filter(or_(
                AppManagerDashboard.user_id == None,   # noqa: E711
                AppManagerDashboard.user_id == user.id,
                AppManagerDashboard.role_id.in_(user_role_ids) if user_role_ids else False,
            ))
            db_widgets = q.order_by(AppManagerDashboard.order).all()
            for w in db_widgets:
                try:
                    data = resolve_widget(w)
                    widgets.append({
                        "id":          f"db_{w.id}",
                        "title":       w.label,
                        "widget_type": w.widget_type,
                        "icon":        w.icon or "fa fa-chart-bar",
                        "color":       w.color or "primary",
                        "link":        w.link_url,
                        "width":       w.width or 3,
                        **data,
                    })
                except Exception:
                    pass
        except Exception:
            pass

    # Always append built-in system widgets
    try:
        total_users = User.query.count()
        widgets.append({
            "id": "total_users", "title": "Total Users", "value": total_users,
            "icon": "fa fa-users", "color": "primary",
            "link": "/admin/users", "link_label": "View all",
        })
    except Exception:
        pass

    try:
        unread_act = user.new_activities() if hasattr(user, "new_activities") else 0
        widgets.append({
            "id": "new_activities", "title": "New Log Entries", "value": unread_act,
            "icon": "fa fa-bolt", "color": "info",
            "link": "/admin/user-log", "link_label": "View log",
        })
    except Exception:
        pass

    try:
        from arasCore.arasAdmin.models import AppManagerApp
        total_apps = AppManagerApp.query.filter_by(is_active=True).count()
        widgets.append({
            "id": "active_apps", "title": "Active Apps", "value": total_apps,
            "icon": "fa fa-cubes", "color": "secondary",
            "link": "/admin/apps", "link_label": "Manage",
        })
    except Exception:
        pass

    return widgets
