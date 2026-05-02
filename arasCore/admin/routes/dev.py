# -*- coding: utf-8 -*-
import re
from flask import render_template, request, jsonify, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import text, inspect
import importlib

from arasCore.admin import admin_bp
from arasCore.lib.core.extensions import db


def _is_dev_authorized():
    """Check if user is authorized for destructive/low-level dev tools."""
    if current_app.debug:
        return True
    if current_user.is_authenticated:
        if current_user.is_admin or current_user.has_role("SUPERADMIN"):
            return True
    return False


@admin_bp.route("/dev")
@login_required
def dev():
    import sys as _sys
    import inspect as _inspect
    
    routes = []
    for rule in sorted(current_app.url_map.iter_rules(), key=lambda r: r.rule):
        handler = current_app.view_functions.get(rule.endpoint)
        doc = _inspect.getdoc(handler) or "No documentation."
        
        # Try to guess app/blueprint
        parts = rule.endpoint.split(".")
        blueprint = parts[0] if len(parts) > 1 else "root"
        
        routes.append({
            "rule":     rule.rule,
            "endpoint": rule.endpoint,
            "methods":  list(sorted(m for m in rule.methods if m not in ("HEAD", "OPTIONS"))),
            "blueprint": blueprint,
            "doc":       doc,
            "file":      _inspect.getfile(handler) if handler else "unknown"
        })
        
    modules = sorted(k for k in _sys.modules if k.startswith("arasCore") or k.startswith("aras."))
    return render_template(
        "admin/setting/setting_dev_standalone.html",
        main_title="Developer Tools",
        routes=routes,
        modules=modules,
    )


@admin_bp.route("/dev/components")
@login_required
def dev_components():
    return render_template(
        "admin/setting/setting_components.html",
        main_title="Component Catalog"
    )


@admin_bp.route("/dev/logs")
@login_required
def dev_logs():
    return render_template(
        "admin/setting/setting_logs.html",
        main_title="Log Viewer"
    )


@admin_bp.route("/api/dev/logs")
@login_required
def api_dev_logs():
    import os
    
    level = request.args.get("level", "").upper()
    search = request.args.get("search", "").lower()
    limit = int(request.args.get("limit", 100))
    
    log_file = current_app.config.get("LOGGING_FILE")
    if not log_file or not os.path.exists(log_file):
        return jsonify({"error": "Log file not found", "path": log_file}), 404
        
    logs = []
    try:
        with open(log_file, "r") as f:
            lines = f.readlines()
            for line in reversed(lines):
                if not line.strip():
                    continue
                parts = line.split(" — ")
                if len(parts) >= 5:
                    log_level = parts[2].strip()
                    message = " — ".join(parts[4:]).strip()
                    if level and level != log_level:
                        continue
                    if search and search not in line.lower():
                        continue
                    logs.append({
                        "timestamp": parts[0].strip(),
                        "logger": parts[1].strip(),
                        "level": log_level,
                        "source": parts[3].strip(),
                        "message": message,
                        "raw": line.strip()
                    })
                    if len(logs) >= limit:
                        break
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"logs": logs})


# ── B.8 SQL Console ───────────────────────────────────────────────────────────

@admin_bp.route("/dev/sql")
@login_required
def dev_sql():
    if not _is_dev_authorized():
        flash("Unauthorized. Debug mode or SUPERADMIN role required.", "danger")
        return redirect(url_for("admin.dev"))
    return render_template(
        "admin/setting/setting_sql_console.html",
        main_title="SQL Console"
    )


@admin_bp.route("/api/dev/sql/execute", methods=["POST"])
@login_required
def api_dev_sql_execute():
    if not _is_dev_authorized():
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json or {}
    query = (data.get("query") or "").strip()
    
    if not query:
        return jsonify({"error": "Query is empty"}), 400

    # Read-only validation: Must start with SELECT (case-insensitive)
    # and not contain forbidden words like INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, REPLACE
    forbidden = r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|REPLACE|GRANT|REVOKE)\b"
    if not re.match(r"^\s*SELECT\b", query, re.I):
        return jsonify({"error": "Only SELECT queries are allowed."}), 400
    if re.search(forbidden, query, re.I):
        return jsonify({"error": "Forbidden command detected in query."}), 400

    try:
        result = db.session.execute(text(query))
        
        # Limit result to 1000 for safety if no LIMIT was provided
        # (Very simple check, doesn't handle nested queries well but good enough for a dev tool)
        if "LIMIT" not in query.upper() and result.returns_rows:
            # We can't easily add LIMIT to a complex query string, so we just slice the fetch
            rows = result.fetchmany(1001)
            is_truncated = len(rows) > 1000
            rows = rows[:1000]
        else:
            rows = result.fetchall()
            is_truncated = False

        columns = list(result.keys())
        data_list = [dict(zip(columns, row)) for row in rows]
        
        return jsonify({
            "columns": columns,
            "rows": data_list,
            "count": len(data_list),
            "truncated": is_truncated
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── B.9 Manifest ↔ DB Sync GUI ────────────────────────────────────────────────

@admin_bp.route("/dev/sync")
@login_required
def dev_sync():
    from arasCore.admin.models import AppManagerApp, AppManagerTable
    from arasCore.lib.services.app_helper import AppHelper
    from arasCore.lib.services.blueprints import get_helper_registry
    
    apps = AppManagerApp.query.all()
    app_list = []
    
    helper_registry = get_helper_registry()
    
    for a in apps:
        helper = helper_registry.get(a.slug)
        if not helper:
            pkg_name = f"aras.{a.slug}"
            try:
                mod = importlib.import_module(f"{pkg_name}.manifest")
                helper = getattr(mod, "helper", None)
            except ModuleNotFoundError:
                helper = None
        
        status = "Unknown"
        drift_details = []
        
        if helper and isinstance(helper, AppHelper):
            # Check for drift
            mgr_tables = AppManagerTable.query.filter_by(app_id=a.id).all()
            mgr_table_names = {t.name for t in mgr_tables}
            
            manifest_table_names = set()
            for r in (helper.resources or []):
                manifest_table_names.add(r.name)
            for g in (helper.menu_groups or []):
                for r in g.resources:
                    manifest_table_names.add(r.name)
            
            missing_in_db = manifest_table_names - mgr_table_names
            extra_in_db = mgr_table_names - manifest_table_names - {"_settings"} # _settings is auto-added
            # Filter groups which start with _group_
            extra_in_db = {n for n in extra_in_db if not n.startswith("_group_")}

            if missing_in_db:
                drift_details.append(f"Missing tables: {', '.join(missing_in_db)}")
            if extra_in_db:
                drift_details.append(f"Stale tables: {', '.join(extra_in_db)}")
                
            status = "Drift" if drift_details else "Synced"
        else:
            status = "No Manifest"
            
        app_list.append({
            "id": a.id,
            "slug": a.slug,
            "title": a.title,
            "status": status,
            "drift_details": drift_details,
            "has_helper": helper is not None
        })
        
    return render_template(
        "admin/setting/setting_sync.html",
        main_title="Manifest Sync",
        apps=app_list
    )


@admin_bp.route("/api/dev/sync/app/<int:app_id>", methods=["POST"])
@login_required
def api_dev_sync_app(app_id):
    if not _is_dev_authorized():
        return jsonify({"error": "Unauthorized"}), 403
        
    from arasCore.admin.models import AppManagerApp
    from arasCore.lib.services.installer import sync_helper_to_db
    from arasCore.lib.services.app_helper import AppHelper
    from arasCore.lib.services.blueprints import get_helper_registry
    
    app_obj = AppManagerApp.query.get_or_404(app_id)
    helper = get_helper_registry().get(app_obj.slug)
    
    if not helper:
        pkg_name = f"aras.{app_obj.slug}"
        try:
            mod = importlib.import_module(f"{pkg_name}.manifest")
            helper = getattr(mod, "helper", None)
        except ModuleNotFoundError:
            return jsonify({"error": "Manifest not found"}), 404
            
    if not isinstance(helper, AppHelper):
        return jsonify({"error": "Invalid AppHelper manifest"}), 400
        
    try:
        _, stats = sync_helper_to_db(helper, db, current_app._get_current_object())
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
