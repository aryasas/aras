# -*- coding: utf-8 -*-
import os
import sys
import json as _json
from datetime import datetime as _dt

from flask import render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from arasCore.arasAdmin import arasAdmin_bp
from arasCore.lib.extensions import db
from arasCore.auth import User


@arasAdmin_bp.route("/settings")
@login_required
def settings():
    from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable
    from arasCore.permissions import Role, Permission
    from sqlalchemy import inspect as sa_inspect

    q_apps     = request.args.get("q_apps", "").strip()
    q_doctypes = request.args.get("q_doctypes", "").strip()
    q_users    = request.args.get("q_users", "").strip()
    q_userlog  = request.args.get("q_userlog", "").strip()
    q_roles    = request.args.get("q_roles", "").strip()

    apps_q = AppManagerApp.query.order_by(AppManagerApp.id)
    if q_apps:
        like = f"%{q_apps}%"
        apps_q = apps_q.filter(
            db.or_(AppManagerApp.url.ilike(like), AppManagerApp.title.ilike(like))
        )
    all_apps = apps_q.all()

    users_q = User.query.order_by(User.created_at.desc())
    if q_users:
        like = f"%{q_users}%"
        users_q = users_q.filter(
            db.or_(User.username.ilike(like), User.email.ilike(like))
        )
    all_users = users_q.all()

    roles_q = Role.query.order_by(Role.name)
    if q_roles:
        like = f"%{q_roles}%"
        roles_q = roles_q.filter(
            db.or_(Role.name.ilike(like), Role.slug.ilike(like))
        )
    all_roles = roles_q.all()
    all_permissions = Permission.query.order_by(Permission.app_slug, Permission.slug).all()

    tables_q = (
        AppManagerTable.query
        .join(AppManagerApp, AppManagerTable.app_id == AppManagerApp.id)
        .order_by(AppManagerApp.url, AppManagerTable.menu_order)
    )
    if q_doctypes:
        like = f"%{q_doctypes}%"
        tables_q = tables_q.filter(
            db.or_(AppManagerTable.name.ilike(like), AppManagerApp.url.ilike(like))
        )
    all_tables = tables_q.all()

    db_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
    try:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(db_uri)
        masked = parsed._replace(
            netloc=parsed.netloc.replace(parsed.password or "", "***") if parsed.password else parsed.netloc
        )
        db_uri_display = urlunparse(masked)
    except Exception:
        db_uri_display = db_uri

    from types import SimpleNamespace
    q_database = request.args.get("q_database", "").strip()
    db_tables = []
    try:
        inspector = sa_inspect(db.engine)
        for tname in inspector.get_table_names():
            if q_database and q_database.lower() not in tname.lower():
                continue
            cols = [c["name"] for c in inspector.get_columns(tname)]
            db_tables.append(SimpleNamespace(
                id=tname,
                name=tname,
                columns=", ".join(cols),
                edit_url=f"/admin/settings/db/{tname}/",
            ))
    except Exception as e:
        current_app.logger.warning(f"DB inspect error: {e}")

    from arasCore.lib.server_config import load as load_server_cfg
    _start = current_app.config.get("_SERVER_START_TIME")
    if _start:
        delta = _dt.utcnow() - _start
        h, rem = divmod(int(delta.total_seconds()), 3600)
        m, s   = divmod(rem, 60)
        uptime_str = f"{h}h {m}m {s}s"
    else:
        uptime_str = "—"

    server_info = {
        "env":            current_app.config.get("ENV", "production"),
        "debug":          current_app.debug,
        "python_version": sys.version.split()[0],
        "host":           request.host,
        "server_time":    _dt.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "uptime":         uptime_str,
    }
    server_cfg = load_server_cfg(current_app._get_current_object())

    upload_folders = {
        "UPLOAD_FOLDER":       current_app.config.get("UPLOAD_FOLDER", ""),
        "UPLOAD_IMAGE_FOLDER": current_app.config.get("UPLOAD_IMAGE_FOLDER", ""),
        "UPLOAD_DOC_FOLDER":   current_app.config.get("UPLOAD_DOC_FOLDER", ""),
        "UPLOAD_PDF_FOLDER":   current_app.config.get("UPLOAD_PDF_FOLDER", ""),
        "UPLOAD_AUDIO_FOLDER": current_app.config.get("UPLOAD_AUDIO_FOLDER", ""),
    }

    from arasCore.arasAdmin.models import UserActivity
    from flask_login import current_user as _cu
    act_q = _cu.activities.order_by(UserActivity.created_at.desc())
    if q_userlog:
        like = f"%{q_userlog}%"
        act_q = act_q.filter(
            db.or_(UserActivity.name.ilike(like), UserActivity.module.ilike(like))
        )
    activities = act_q.limit(200).all()

    return render_template(
        "admin/settings.html",
        title="Settings",
        main_title="Settings",
        apps=all_apps,
        users=all_users,
        all_tables=all_tables,
        db_uri=db_uri_display,
        db_tables=db_tables,
        server_info=server_info,
        server_cfg=server_cfg,
        upload_folders=upload_folders,
        all_roles=all_roles,
        all_permissions=all_permissions,
        activities=activities,
        q_apps=q_apps,
        q_doctypes=q_doctypes,
        q_users=q_users,
        q_userlog=q_userlog,
        q_database=q_database,
        q_roles=q_roles,
    )


@arasAdmin_bp.route("/settings/db/<table_name>/")
@login_required
def db_table_detail(table_name):
    from sqlalchemy import inspect as sa_inspect
    inspector = sa_inspect(db.engine)
    if table_name not in inspector.get_table_names():
        from flask import abort
        abort(404)
    columns = inspector.get_columns(table_name)
    pk_cols = {c for c in inspector.get_pk_constraint(table_name).get("constrained_columns", [])}
    indexes = inspector.get_indexes(table_name)
    return render_template(
        "admin/db_table_detail.html",
        title=table_name,
        main_title=table_name,
        table_name=table_name,
        columns=columns,
        pk_cols=pk_cols,
        indexes=indexes,
    )


@arasAdmin_bp.route("/settings/db/generate-view", methods=["POST"])
@login_required
def db_generate_view():
    from arasCore.arasAdmin.models import AppManagerApp

    table_name = request.form.get("table_name", "").strip()
    if not table_name:
        flash("No table selected.", "warning")
        return redirect(url_for("admin.settings") + "?panel=panel-database")

    existing = AppManagerApp.query.filter_by(url=table_name).first()
    if existing:
        flash(f"App for table '{table_name}' already exists.", "info")
        return redirect(url_for("admin.settings") + "?panel=panel-database")

    slug   = table_name.replace("-", "_")
    title  = slug.replace("_", " ").title()
    app_obj = AppManagerApp(
        url=slug, title=title,
        is_active=False, in_sidebar=True,
    )
    db.session.add(app_obj)
    db.session.commit()
    flash(f"App '{title}' created from table '{table_name}'. Activate it in App Manager.", "success")
    return redirect(url_for("admin.settings") + "?panel=panel-apps")


@arasAdmin_bp.route("/settings/uploads/save", methods=["POST"])
@login_required
def settings_upload_save():
    instance_dir = os.path.join(current_app.root_path, "..", "instance")
    cfg_path     = os.path.join(instance_dir, "server.json")
    try:
        with open(cfg_path) as f:
            cfg = _json.load(f)
    except (FileNotFoundError, ValueError):
        cfg = {}

    keys = ["UPLOAD_FOLDER", "UPLOAD_IMAGE_FOLDER", "UPLOAD_DOC_FOLDER",
            "UPLOAD_PDF_FOLDER", "UPLOAD_AUDIO_FOLDER"]
    for key in keys:
        val = request.form.get(key, "").strip()
        if val:
            cfg[key] = val

    os.makedirs(instance_dir, exist_ok=True)
    with open(cfg_path, "w") as f:
        _json.dump(cfg, f, indent=2)

    flash("Upload paths saved. Restart server to apply.", "success")
    return redirect(url_for("admin.settings") + "?panel=panel-uploads")


@arasAdmin_bp.route("/settings/uploads/test", methods=["POST"])
@login_required
def settings_upload_test():
    folder_key = request.form.get("folder_key", "UPLOAD_FOLDER")
    folder     = current_app.config.get(folder_key, "")
    f          = request.files.get("test_file")

    if not f or not f.filename:
        flash("No file selected.", "warning")
        return redirect(url_for("admin.settings") + "?panel=panel-uploads")
    if not folder:
        flash(f"{folder_key} is not configured.", "danger")
        return redirect(url_for("admin.settings") + "?panel=panel-uploads")

    os.makedirs(folder, exist_ok=True)
    filename = secure_filename(f.filename)
    dest = os.path.join(folder, filename)
    f.save(dest)
    flash(f"File saved: {dest}", "success")
    return redirect(url_for("admin.settings") + "?panel=panel-uploads")


@arasAdmin_bp.route("/settings/server/save", methods=["POST"])
@login_required
def server_settings_save():
    from arasCore.lib.server_config import save as save_server_cfg
    data = {
        "wsgi_server":  request.form.get("wsgi_server", "gunicorn"),
        "host":         request.form.get("host", "0.0.0.0"),
        "port":         request.form.get("port", 8080),
        "workers":      request.form.get("workers", 2),
        "threads":      request.form.get("threads", 2),
        "worker_class": request.form.get("worker_class", "sync"),
        "timeout":      request.form.get("timeout", 30),
        "keepalive":    request.form.get("keepalive", 2),
        "max_requests": request.form.get("max_requests", 1000),
        "ssl_enabled":  request.form.get("ssl_enabled") == "1",
        "ssl_certfile": request.form.get("ssl_certfile", ""),
        "ssl_keyfile":  request.form.get("ssl_keyfile", ""),
        "loglevel":     request.form.get("loglevel", "info"),
        "accesslog":    request.form.get("accesslog", "-"),
        "errorlog":     request.form.get("errorlog", "-"),
    }
    save_server_cfg(current_app._get_current_object(), data)
    flash("Server settings saved. Restart to apply.", "success")
    return redirect(url_for("admin.settings") + "?panel=panel-server")


@arasAdmin_bp.route("/settings/server/restart", methods=["POST"])
@login_required
def server_restart():
    from arasCore.lib.server_config import restart_server
    flash("Server restart initiated.", "info")
    restart_server()
    return redirect(url_for("admin.settings") + "?panel=panel-server")


# ── Roles & Permissions ───────────────────────────────────────────────────────

@arasAdmin_bp.route("/roles/new", methods=["POST"])
@login_required
def role_new():
    from arasCore.permissions import Role
    name = (request.form.get("name") or "").strip()
    slug = (request.form.get("slug") or name.lower().replace(" ", "_")).strip()
    desc = request.form.get("description") or None
    if not name or not slug:
        flash("Name and slug are required.", "warning")
    elif Role.query.filter_by(slug=slug).first():
        flash(f"Role '{slug}' already exists.", "warning")
    else:
        db.session.add(Role(name=name, slug=slug, description=desc))
        db.session.commit()
        flash(f"Role '{name}' created.", "success")
    return redirect(url_for("admin.settings") + "?panel=panel-roles")


@arasAdmin_bp.route("/roles/<int:role_id>/delete", methods=["POST"])
@login_required
def role_delete(role_id):
    from arasCore.permissions import Role
    role = Role.query.get_or_404(role_id)
    db.session.delete(role)
    db.session.commit()
    flash(f"Role '{role.name}' deleted.", "warning")
    return redirect(url_for("admin.settings") + "?panel=panel-roles")


@arasAdmin_bp.route("/roles/bulk-delete/", methods=["POST"])
@login_required
def roles_bulk_delete():
    from arasCore.permissions import Role
    ids_raw = request.form.get("ids", "")
    ids = [int(i) for i in ids_raw.split(",") if i.strip().isdigit()]
    deleted = 0
    for rid in ids:
        role = Role.query.get(rid)
        if role:
            db.session.delete(role)
            deleted += 1
    db.session.commit()
    flash(f"Deleted {deleted} role(s).", "danger")
    return redirect(url_for("admin.settings") + "?panel=panel-roles")


@arasAdmin_bp.route("/roles/<int:role_id>/toggle", methods=["POST"])
@login_required
def role_toggle(role_id):
    from arasCore.permissions import Role
    role = Role.query.get_or_404(role_id)
    role.is_active = not role.is_active
    db.session.commit()
    return redirect(url_for("admin.settings") + "?panel=panel-roles")


@arasAdmin_bp.route("/roles/<int:role_id>/permissions", methods=["POST"])
@login_required
def role_permissions_save(role_id):
    from arasCore.permissions import Role, Permission
    role     = Role.query.get_or_404(role_id)
    perm_ids = [int(x) for x in request.form.getlist("perm_ids")]
    role.permissions = Permission.query.filter(Permission.id.in_(perm_ids)).all()
    db.session.commit()
    flash("Permissions updated.", "success")
    return redirect(url_for("admin.settings") + "?panel=panel-roles")


@arasAdmin_bp.route("/roles/<int:role_id>/users", methods=["POST"])
@login_required
def role_users_save(role_id):
    from arasCore.permissions import Role, UserRole
    role     = Role.query.get_or_404(role_id)
    user_ids = [int(x) for x in request.form.getlist("user_ids")]
    app_slug = request.form.get("app_slug") or None
    UserRole.query.filter_by(role_id=role_id, app_slug=app_slug).delete()
    for uid in user_ids:
        db.session.add(UserRole(user_id=uid, role_id=role_id, app_slug=app_slug))
    db.session.commit()
    flash("User assignments updated.", "success")
    return redirect(url_for("admin.settings") + "?panel=panel-roles")


@arasAdmin_bp.route("/roles/<int:role_id>/", methods=["GET", "POST"])
@arasAdmin_bp.route("/roles/<int:role_id>/edit", methods=["GET", "POST"])
@login_required
def role_edit(role_id):
    from arasCore.permissions import Role, Permission, UserRole
    role = Role.query.get_or_404(role_id)
    all_permissions = Permission.query.order_by(Permission.app_slug, Permission.slug).all()
    all_users = User.query.order_by(User.username).all()

    if request.method == "POST":
        action = request.form.get("_action")
        if action == "permissions":
            perm_ids = [int(x) for x in request.form.getlist("perm_ids")]
            role.permissions = [p for p in all_permissions if p.id in perm_ids]
            db.session.commit()
            flash("Permissions updated.", "success")
        elif action == "users":
            user_ids = [int(x) for x in request.form.getlist("user_ids")]
            UserRole.query.filter_by(role_id=role_id).delete()
            for uid in user_ids:
                db.session.add(UserRole(user_id=uid, role_id=role_id))
            db.session.commit()
            flash("Users updated.", "success")
        return redirect(url_for("admin.role_edit", role_id=role_id))

    role_perm_ids = [p.id for p in role.permissions]
    assigned_user_ids = [ur.user_id for ur in UserRole.query.filter_by(role_id=role_id).all()]
    grouped_perms = {}
    for p in all_permissions:
        grouped_perms.setdefault(p.app_slug, []).append(p)

    return render_template(
        "admin/role_edit.html",
        title=f"Edit Role — {role.name}",
        main_title="Roles",
        role=role,
        all_permissions=all_permissions,
        grouped_perms=grouped_perms,
        role_perm_ids=role_perm_ids,
        all_users=all_users,
        assigned_user_ids=assigned_user_ids,
        list_url=url_for("admin.settings") + "?panel=panel-roles",
    )


@arasAdmin_bp.route("/settings/menu/data")
@login_required
def menu_data():
    from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable

    def node_dict(t):
        return {
            "id":           t.id,
            "name":         t.name,
            "title":        t.get_menu_title(),
            "icon":         t.menu_icon or "fa-table",
            "show_in_menu": t.show_in_menu,
            "menu_order":   t.menu_order,
            "db_backed":    True,
            "is_group":     t.page_type == "group",
            "children":     [],
        }

    result = []
    for app in AppManagerApp.query.order_by(AppManagerApp.menu_order).all():
        tables = (AppManagerTable.query
                  .filter_by(app_id=app.id)
                  .order_by(AppManagerTable.menu_order)
                  .all())
        tbl_map = {t.id: node_dict(t) for t in tables}
        roots = []
        for t in tables:
            node = tbl_map[t.id]
            if t.parent_table_id and t.parent_table_id in tbl_map:
                tbl_map[t.parent_table_id]["children"].append(node)
            else:
                roots.append(node)
        result.append({
            "id":         app.id,
            "name":       app.name,
            "title":      app.main_title,
            "icon":       app.icon or "fa-cubes",
            "menu_order": app.menu_order or 0,
            "in_sidebar": app.in_sidebar,
            "db_backed":  True,
            "tables":     roots,
        })
    return jsonify(result)


@arasAdmin_bp.route("/settings/menu/save", methods=["POST"])
@login_required
def menu_save():
    from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable
    from arasCore.arasAdmin.services import clear_cache
    data = request.get_json(force=True)
    try:
        for app_node in data.get("apps", []):
            aid = int(app_node.get("id", 0))
            if aid <= 0:
                continue
            app = db.session.get(AppManagerApp, aid)
            if not app:
                continue
            app.menu_order = int(app_node.get("menu_order") or 0)
            app.main_title = app_node.get("title") or app.main_title
            app.icon       = app_node.get("icon") or app.icon
            app.in_sidebar = bool(app_node.get("in_sidebar", True))

        def save_table_nodes(nodes, parent_id=None):
            for order, node in enumerate(nodes):
                nid = int(node.get("id") or 0)
                if nid > 0:
                    tbl = db.session.get(AppManagerTable, nid)
                    if tbl:
                        tbl.menu_order      = order
                        tbl.menu_title      = node.get("title") or None
                        tbl.menu_icon       = node.get("icon") or tbl.menu_icon
                        tbl.show_in_menu    = bool(node.get("show_in_menu", True))
                        tbl.parent_table_id = parent_id
                save_table_nodes(node.get("children", []),
                                 nid if nid > 0 else parent_id)

        for app_node in data.get("apps", []):
            save_table_nodes(app_node.get("tables", []), None)

        db.session.commit()
        clear_cache()
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("menu_save error")
        return jsonify({"ok": False, "error": repr(e)}), 500


@arasAdmin_bp.route("/settings/menu/add-group", methods=["POST"])
@login_required
def menu_add_group():
    from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable
    from arasCore.arasAdmin.services import clear_cache
    data = request.get_json(force=True)
    app_id = int(data.get("app_id") or 0)
    title  = (data.get("title") or "").strip()
    icon   = (data.get("icon") or "fa-folder").strip()
    if not app_id or not title:
        return jsonify({"ok": False, "error": "app_id and title required"}), 400
    app = db.session.get(AppManagerApp, app_id)
    if not app:
        return jsonify({"ok": False, "error": "app not found"}), 404
    slug = title.lower().replace(" ", "-")
    existing = AppManagerTable.query.filter_by(app_id=app_id, name=f"_grp_{slug}").first()
    if existing:
        return jsonify({"ok": False, "error": "group with this title already exists"}), 409
    from sqlalchemy import select as _select, func as _func
    max_order = db.session.execute(
        _select(_func.max(AppManagerTable.menu_order)).where(AppManagerTable.app_id == app_id)
    ).scalar() or 0
    grp = AppManagerTable(
        app_id=app_id, name=f"_grp_{slug}", title=title,
        menu_title=title, menu_icon=icon,
        page_type="group", url_suffix=f"/{slug}",
        db_table_name=None, show_in_menu=True,
        menu_order=max_order + 10, is_active=True,
    )
    db.session.add(grp)
    db.session.commit()
    clear_cache()
    return jsonify({"ok": True, "id": grp.id, "title": title, "icon": icon})


@arasAdmin_bp.route("/settings/menu/add-page", methods=["POST"])
@login_required
def menu_add_page():
    from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable
    from arasCore.arasAdmin.services import clear_cache
    data    = request.get_json(force=True)
    app_id  = int(data.get("app_id") or 0)
    title   = (data.get("title") or "").strip()
    icon    = (data.get("icon") or "fa-file").strip()
    url_suffix = (data.get("url_suffix") or "").strip()
    parent_id  = data.get("parent_id")
    if parent_id:
        parent_id = int(parent_id)
    if not app_id or not title or not url_suffix:
        return jsonify({"ok": False, "error": "app_id, title, and url_suffix required"}), 400
    app = db.session.get(AppManagerApp, app_id)
    if not app:
        return jsonify({"ok": False, "error": "app not found"}), 404
    slug = url_suffix.strip("/").replace("/", "-")
    name = f"_page_{slug}"
    existing = AppManagerTable.query.filter_by(app_id=app_id, name=name).first()
    if existing:
        return jsonify({"ok": False, "error": "page with this url_suffix already exists"}), 409
    from sqlalchemy import select as _select, func as _func
    max_order = db.session.execute(
        _select(_func.max(AppManagerTable.menu_order)).where(AppManagerTable.app_id == app_id)
    ).scalar() or 0
    page = AppManagerTable(
        app_id=app_id, name=name, title=title,
        menu_title=title, menu_icon=icon,
        page_type="list", url_suffix=url_suffix,
        db_table_name=None, show_in_menu=True,
        menu_order=max_order + 10, is_active=True,
        parent_table_id=parent_id,
    )
    db.session.add(page)
    db.session.commit()
    clear_cache()
    return jsonify({"ok": True, "id": page.id, "title": title, "icon": icon})


@arasAdmin_bp.route("/settings/menu/delete/<int:table_id>", methods=["POST"])
@login_required
def menu_delete_item(table_id):
    from arasCore.arasAdmin.models import AppManagerTable
    from arasCore.arasAdmin.services import clear_cache
    tbl = db.session.get(AppManagerTable, table_id)
    if not tbl:
        return jsonify({"ok": False, "error": "not found"}), 404
    # Re-parent children to this item's parent before deleting
    AppManagerTable.query.filter_by(parent_table_id=tbl.id).update(
        {"parent_table_id": tbl.parent_table_id}
    )
    db.session.delete(tbl)
    db.session.commit()
    clear_cache()
    return jsonify({"ok": True})
