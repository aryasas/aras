# -*- coding: utf-8 -*-
import sys
from datetime import datetime as _dt
from flask import render_template, request, current_app
from flask_login import login_required
from arasCore.admin import admin_bp
from arasCore.lib.core.extensions import db
from arasCore.auth import User

@admin_bp.route("/settings")
@login_required
def settings():
    from arasCore.admin.models import AppManagerApp, AppManagerTable
    from arasCore.permissions import Role, Permission
    from sqlalchemy import inspect as sa_inspect
    from arasCore.lib.core.server_config import load as load_server_cfg
    from arasCore.admin.models import UserActivity, ArasCoreAuditLog, ArasSystemSetting
    from arasCore.lib.models.webhook_models import WebhookEndpoint
    from arasCore.lib.models.script_models import SrvScript
    from flask_login import current_user as _cu
    from types import SimpleNamespace

    q_apps     = request.args.get("q_apps", "").strip()
    q_doctypes = request.args.get("q_doctypes", "").strip()
    q_users    = request.args.get("q_users", "").strip()
    q_userlog  = request.args.get("q_userlog", "").strip()
    q_roles    = request.args.get("q_roles", "").strip()

    # Apps
    apps_q = AppManagerApp.query.order_by(AppManagerApp.id)
    if q_apps:
        like = f"%{q_apps}%"
        apps_q = apps_q.filter(db.or_(AppManagerApp.url.ilike(like), AppManagerApp.title.ilike(like)))
    all_apps = apps_q.all()

    # Users
    users_q = User.query.order_by(User.created_at.desc())
    if q_users:
        like = f"%{q_users}%"
        users_q = users_q.filter(db.or_(User.username.ilike(like), User.email.ilike(like)))
    all_users = users_q.all()

    # Roles
    roles_q = Role.query.order_by(Role.name)
    if q_roles:
        like = f"%{q_roles}%"
        roles_q = roles_q.filter(db.or_(Role.name.ilike(like), Role.slug.ilike(like)))
    all_roles = roles_q.all()
    all_permissions = Permission.query.order_by(Permission.app_slug, Permission.slug).all()

    # DocTypes
    tables_q = (AppManagerTable.query
                .join(AppManagerApp, AppManagerTable.app_id == AppManagerApp.id)
                .order_by(AppManagerApp.url, AppManagerTable.menu_order))
    if q_doctypes:
        like = f"%{q_doctypes}%"
        tables_q = tables_q.filter(db.or_(AppManagerTable.name.ilike(like), AppManagerApp.url.ilike(like)))
    all_tables = tables_q.all()

    # Server Info
    _start = current_app.config.get("_SERVER_START_TIME")
    uptime_str = "—"
    if _start:
        delta = _dt.utcnow() - _start
        h, rem = divmod(int(delta.total_seconds()), 3600)
        m, s   = divmod(rem, 60)
        uptime_str = f"{h}h {m}m {s}s"

    server_info = {
        "env":            __import__("os").environ.get("FLASK_ENV", "development" if current_app.debug else "production"),
        "debug":          current_app.debug,
        "python_version": sys.version.split()[0],
        "host":           request.host,
        "server_time":    _dt.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "uptime":         uptime_str,
    }
    server_cfg = load_server_cfg(current_app._get_current_object())

    # Database
    db_tables = []
    try:
        inspector = sa_inspect(db.engine)
        q_database = request.args.get("q_database", "").strip()
        for tname in inspector.get_table_names():
            if q_database and q_database.lower() not in tname.lower(): continue
            cols = [c["name"] for c in inspector.get_columns(tname)]
            db_tables.append(SimpleNamespace(id=tname, name=tname, columns=", ".join(cols)))
    except Exception: pass

    # Activity Log
    act_q = _cu.activities.order_by(UserActivity.created_at.desc())
    if q_userlog:
        like = f"%{q_userlog}%"
        act_q = act_q.filter(db.or_(UserActivity.name.ilike(like), UserActivity.module.ilike(like)))
    activities = act_q.limit(200).all()

    # Audit Log
    q_audit = request.args.get("q_audit", "").strip()
    audit_q = ArasCoreAuditLog.query.order_by(ArasCoreAuditLog.ts.desc())
    if q_audit:
        like = f"%{q_audit}%"
        audit_q = audit_q.filter(db.or_(ArasCoreAuditLog.model_name.ilike(like), ArasCoreAuditLog.action.ilike(like)))
    audit_logs = audit_q.limit(200).all()
    user_cache = {}
    for entry in audit_logs:
        if entry.user_id and entry.user_id not in user_cache:
            u = User.query.get(entry.user_id)
            user_cache[entry.user_id] = u.username if u else f"#{entry.user_id}"
        entry._username = user_cache.get(entry.user_id, "system") if entry.user_id else "system"

    from arasCore.lib.services.workflow import _workflow_registry
    from arasCore.lib.core.health import _last_result as health_data

    # Fetch theme tokens from ArasSystemSetting
    theme_tokens_json = ArasSystemSetting.get("core.theme_tokens", "{}")
    if isinstance(theme_tokens_json, str):
        import json
        try:
            theme_tokens = json.loads(theme_tokens_json)
        except:
            theme_tokens = {}
    else:
        theme_tokens = theme_tokens_json

    return render_template(
        "admin/setting/setting_settings.html",
        title="Settings", main_title="Settings",
        apps=all_apps, users=all_users, all_roles=all_roles,
        all_permissions=all_permissions, all_tables=all_tables,
        server_info=server_info, server_cfg=server_cfg,
        db_tables=db_tables, activities=activities, audit_logs=audit_logs,
        q_audit=q_audit, health_data=health_data,
        dev_routes=[], # Simplified for now
        workflows=_workflow_registry,
        system_settings=ArasSystemSetting.query.order_by(ArasSystemSetting.section, ArasSystemSetting.key).all(),
        webhook_endpoints=WebhookEndpoint.query.all(),
        server_scripts=SrvScript.query.all(),
        upload_folders={k: current_app.config.get(k, "") for k in ["UPLOAD_FOLDER", "UPLOAD_IMAGE_FOLDER", "UPLOAD_DOC_FOLDER", "UPLOAD_PDF_FOLDER", "UPLOAD_AUDIO_FOLDER"]},
        theme_tokens=theme_tokens
    )


@admin_bp.route("/settings/theme")
@login_required
def settings_theme():
    from arasCore.admin.models import ArasSystemSetting
    import json
    
    tokens_raw = ArasSystemSetting.get("core.theme_tokens", "{}")
    if isinstance(tokens_raw, str):
        try:
            tokens = json.loads(tokens_raw)
        except:
            tokens = {}
    else:
        tokens = tokens_raw
        
    return render_template(
        "admin/setting/setting_theme.html",
        main_title="Theme Customizer",
        tokens=tokens
    )


@admin_bp.route("/settings/theme/preview")
@login_required
def settings_theme_preview():
    return render_template("admin/setting/setting_theme_preview.html")


@admin_bp.route("/api/settings/theme/save", methods=["POST"])
@login_required
def api_settings_theme_save():
    from arasCore.admin.models import ArasSystemSetting
    from flask import jsonify
    
    data = request.json or {}
    # Validation could be added here
    
    ArasSystemSetting.set(
        "core.theme_tokens", 
        data, 
        value_type="json", 
        label="Theme Design Tokens",
        section="appearance"
    )
    
    return jsonify({"success": True})
