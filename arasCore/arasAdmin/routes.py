# -*- coding: utf-8 -*-
"""arasCore/arasAdmin/routes.py — Admin routes (migrated from app_admin/routes.py)."""
from datetime import datetime

from flask import render_template, request, jsonify, redirect, url_for, flash, g, current_app
from flask_login import login_required, current_user

from . import arasAdmin_bp
from .models import UserActivity
from .forms import AppManagerAppForm, CreateUserForm
from .services import get_dashboard_widgets, build_sidebar_menu
from arasCore.lib.extensions import db
from arasCore.auth import User


# ── Before request ────────────────────────────────────────────────────────────

@arasAdmin_bp.before_app_request
def before_request():
    g.user = current_user
    if current_user.is_authenticated:
        # g.messages   = current_user.messages_received.order_by(Message.timestamp.desc())
        g.activities = current_user.activities.order_by(UserActivity.created_at.desc())
        g.gmenu = build_sidebar_menu()


# ── Dashboard ─────────────────────────────────────────────────────────────────

@arasAdmin_bp.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    # form = PostForm()
    # if form.validate_on_submit():
    #     post = Post(body=form.post.data, user_id=current_user.id)
    #     db.session.add(post)
    #     db.session.commit()
    #     flash("Your post is now live!", "success")
    #     return redirect(url_for("admin.dashboard"))

    # page   = request.args.get("page", 1, type=int)
    # per_pg = current_app.config.get("POSTS_PER_PAGE", 10)
    # posts  = Post.query.order_by(Post.timestamp.desc()).paginate(page=page, per_page=per_pg, error_out=False)

    # next_url = url_for("admin.dashboard", page=posts.next_num) if posts.has_next else None
    # prev_url = url_for("admin.dashboard", page=posts.prev_num) if posts.has_prev else None

    widgets = get_dashboard_widgets(current_user)

    return render_template(
        "admin/dashboard.html",
        title="Dashboard",
        main_title="Admin Dashboard",
        # form=form,
        # posts=posts.items,
        # post=posts,
        user=current_user,
        # next_url=next_url,
        # prev_url=prev_url,
        widgets=widgets,
    )


# ── Dev page ──────────────────────────────────────────────────────────────────

@arasAdmin_bp.route("/dev")
@login_required
def dev():
    return render_template("admin/dev.html", main_title="Dev Page", user=current_user)



# ── Messages ──────────────────────────────────────────────────────────────────

# @arasAdmin_bp.route("/send_message/<recipient>", methods=["GET", "POST"])
# @login_required
# def send_message(recipient):
#     user = User.query.filter_by(username=recipient).first_or_404()
#     form = MessageForm()
#     if form.validate_on_submit():
#         msg = Message(sender_id=current_user.id, recipient_id=user.id, body=form.message.data)
#         db.session.add(msg)
#         user.add_notification("unread_message_count", user.new_messages(), category="message")
#         db.session.commit()
#         flash("Your message has been sent.", "success")
#         return redirect(url_for("admin.messages"))
#     return render_template(
#         "admin/send_message.html",
#         title="Send Message",
#         main_title="Message",
#         form=form,
#         recipient=recipient,
#     )


# @arasAdmin_bp.route("/messages")
# @login_required
# def messages():
#     current_user.last_message_read_time = datetime.utcnow()
#     current_user.add_notification("unread_message_count", 0, category="message")
#     db.session.commit()

#     per_pg   = current_app.config.get("POSTS_PER_PAGE", 10)
#     page     = request.args.get("page", 1, type=int)
#     messages = current_user.messages_received.order_by(Message.timestamp.desc()).paginate(
#         page=page, per_page=per_pg, error_out=False
#     )
#     next_url = url_for("admin.messages", page=messages.next_num) if messages.has_next else None
#     prev_url = url_for("admin.messages", page=messages.prev_num) if messages.has_prev else None

#     return render_template(
#         "admin/messages.html",
#         title="Messages",
#         main_title="Messages",
#         messages=messages.items,
#         next_url=next_url,
#         prev_url=prev_url,
#     )


# ── Notifications ─────────────────────────────────────────────────────────────

@arasAdmin_bp.route("/notifications/<category>")
@login_required
def notifications(category):
    since    = request.args.get("since", 0.0, type=float)
    notifs   = (
        current_user.notifications
        .filter(Notification.timestamp > since, Notification.category == category)
        .order_by(Notification.timestamp.asc())
    )
    return jsonify([
        {
            "name":      n.name,
            "data":      n.get_data(),
            "timestamp": n.timestamp,
            "category":  n.category,
        }
        for n in notifs
    ])


# ── User Log ──────────────────────────────────────────────────────────────────

@arasAdmin_bp.route("/user-log", methods=["GET", "POST"])
@login_required
def user_log():
    current_user.last_activity_read_time = datetime.utcnow()
    current_user.add_notification("unread_activity_count", 0, category="activity")
    db.session.commit()
    activities = current_user.activities.order_by(UserActivity.created_at.desc()).all()
    return render_template(
        "admin/user_log.html",
        title="User Log",
        main_title="User Log",
        activities=activities,
    )


# ── Settings ─────────────────────────────────────────────────────────────────

@arasAdmin_bp.route("/settings")
@login_required
def settings():
    from .models import AppManagerApp, AppManagerTable
    from arasCore.lib.extensions import db
    from arasCore.permissions import Role, Permission, UserRole
    from sqlalchemy import inspect as sa_inspect

    all_apps  = AppManagerApp.query.order_by(AppManagerApp.id).all()
    all_users = User.query.order_by(User.created_at.desc()).all()
    all_roles = Role.query.order_by(Role.name).all()
    all_permissions = Permission.query.order_by(Permission.app_slug, Permission.slug).all()

    # DocTypes — all page types grouped by app
    all_tables = (
        AppManagerTable.query
        .join(AppManagerApp, AppManagerTable.app_id == AppManagerApp.id)
        .order_by(AppManagerApp.name, AppManagerTable.menu_order)
        .all()
    )

    # DB info
    db_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
    try:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(db_uri)
        masked = parsed._replace(netloc=parsed.netloc.replace(parsed.password or "", "***") if parsed.password else parsed.netloc)
        db_uri_display = urlunparse(masked)
    except Exception:
        db_uri_display = db_uri

    # Inspect tables
    db_tables = []
    try:
        inspector = sa_inspect(db.engine)
        for tname in inspector.get_table_names():
            cols = [c["name"] for c in inspector.get_columns(tname)]
            db_tables.append({"name": tname, "columns": cols})
    except Exception as e:
        current_app.logger.warning(f"DB inspect error: {e}")

    # Server info + config
    import sys
    from datetime import datetime as _dt
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

    # Upload folder config
    upload_folders = {
        "UPLOAD_FOLDER":       current_app.config.get("UPLOAD_FOLDER", ""),
        "UPLOAD_IMAGE_FOLDER": current_app.config.get("UPLOAD_IMAGE_FOLDER", ""),
        "UPLOAD_DOC_FOLDER":   current_app.config.get("UPLOAD_DOC_FOLDER", ""),
        "UPLOAD_PDF_FOLDER":   current_app.config.get("UPLOAD_PDF_FOLDER", ""),
        "UPLOAD_AUDIO_FOLDER": current_app.config.get("UPLOAD_AUDIO_FOLDER", ""),
    }

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
    )


@arasAdmin_bp.route("/settings/db/generate-view", methods=["POST"])
@login_required
def db_generate_view():
    """Generate an AppManagerApp entry from an existing table."""
    from .models import AppManagerApp
    table_name = request.form.get("table_name", "").strip()
    if not table_name:
        flash("No table selected.", "warning")
        return redirect(url_for("admin.settings") + "#panel-database")

    # Check if already exists
    existing = AppManagerApp.query.filter_by(name=table_name).first()
    if existing:
        flash(f"App for table '{table_name}' already exists.", "info")
        return redirect(url_for("admin.settings") + "#panel-database")

    slug  = table_name.replace("-", "_")
    title = slug.replace("_", " ").title()
    app_obj = AppManagerApp(
        name=slug,
        title=title,
        main_title=title,
        url=f"/{slug.replace('_', '-')}",
        endpoint=slug,
        is_active=False,
        in_sidebar=True,
    )
    from arasCore.lib.extensions import db
    db.session.add(app_obj)
    db.session.commit()
    flash(f"App '{title}' created from table '{table_name}'. Activate it in App Manager.", "success")
    return redirect(url_for("admin.settings") + "#panel-apps")


@arasAdmin_bp.route("/settings/uploads/save", methods=["POST"])
@login_required
def settings_upload_save():
    """Save upload folder paths to instance/server.json."""
    import json as _json
    import os
    instance_dir = os.path.join(current_app.root_path, "..", "instance")
    cfg_path     = os.path.join(instance_dir, "server.json")
    try:
        with open(cfg_path) as f:
            cfg = _json.load(f)
    except (FileNotFoundError, ValueError):
        cfg = {}

    keys = [
        "UPLOAD_FOLDER", "UPLOAD_IMAGE_FOLDER", "UPLOAD_DOC_FOLDER",
        "UPLOAD_PDF_FOLDER", "UPLOAD_AUDIO_FOLDER",
    ]
    for key in keys:
        val = request.form.get(key, "").strip()
        if val:
            cfg[key] = val

    os.makedirs(instance_dir, exist_ok=True)
    with open(cfg_path, "w") as f:
        _json.dump(cfg, f, indent=2)

    flash("Upload paths saved. Restart server to apply.", "success")
    return redirect(url_for("admin.settings") + "#panel-uploads")


@arasAdmin_bp.route("/settings/uploads/test", methods=["POST"])
@login_required
def settings_upload_test():
    """Upload a test file to the selected upload folder."""
    import os
    from werkzeug.utils import secure_filename

    folder_key = request.form.get("folder_key", "UPLOAD_FOLDER")
    folder     = current_app.config.get(folder_key, "")
    f          = request.files.get("test_file")

    if not f or not f.filename:
        flash("No file selected.", "warning")
        return redirect(url_for("admin.settings") + "#panel-uploads")
    if not folder:
        flash(f"{folder_key} is not configured.", "danger")
        return redirect(url_for("admin.settings") + "#panel-uploads")

    os.makedirs(folder, exist_ok=True)
    filename = secure_filename(f.filename)
    dest = os.path.join(folder, filename)
    f.save(dest)
    flash(f"File saved: {dest}", "success")
    return redirect(url_for("admin.settings") + "#panel-uploads")


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
    return redirect(url_for("admin.settings") + "#panel-server")


@arasAdmin_bp.route("/settings/server/restart", methods=["POST"])
@login_required
def server_restart():
    from arasCore.lib.server_config import restart_server
    flash("Server restart initiated.", "info")
    restart_server()
    return redirect(url_for("admin.settings") + "#panel-server")


# ── Apps (App Manager) ────────────────────────────────────────────────────────

@arasAdmin_bp.route("/apps")
@login_required
def apps():
    from .models import AppManagerApp
    all_apps = AppManagerApp.query.order_by(AppManagerApp.id).all()
    return render_template(
        "admin/apps.html",
        title="App Manager",
        main_title="App Manager",
        apps=all_apps,
    )


# ── App Manager — add / edit ──────────────────────────────────────────────────

@arasAdmin_bp.route("/apps/new", methods=["GET", "POST"])
@login_required
def apps_new():
    from .models import AppManagerApp
    form = AppManagerAppForm()
    if form.validate_on_submit():
        app_obj = AppManagerApp(
            name=form.name.data.strip().lower().replace(" ", "_"),
            title=form.title.data,
            main_title=form.main_title.data,
            url=form.url.data.strip(),
            endpoint=form.endpoint.data.strip().lower().replace(" ", "_"),
            description=form.description.data or None,
            icon=form.icon.data,
            color_theme=form.color_theme.data or None,
            is_active=form.is_active.data,
            in_sidebar=form.in_sidebar.data,
            require_login=form.require_login.data,
            api_enabled=form.api_enabled.data,
            items_per_page=form.items_per_page.data or 20,
            export_csv=form.export_csv.data,
            export_excel=form.export_excel.data,
            soft_delete=form.soft_delete.data,
            audit_log=form.audit_log.data,
        )
        db.session.add(app_obj)
        db.session.flush()
        current_user.log_activity("app_created", module="app_manager", payload={"app": app_obj.name})
        db.session.commit()
        flash(f"App '{app_obj.name}' created.", "success")
        return redirect(url_for("admin.apps"))
    return render_template(
        "admin/app_form.html",
        title="New App",
        main_title="New App",
        form=form,
    )


@arasAdmin_bp.route("/apps/<int:app_id>/edit", methods=["GET", "POST"])
@login_required
def apps_edit(app_id):
    from .models import AppManagerApp
    app_obj = AppManagerApp.query.get_or_404(app_id)
    form = AppManagerAppForm(obj=app_obj)
    if form.validate_on_submit():
        app_obj.name          = form.name.data.strip().lower().replace(" ", "_")
        app_obj.title         = form.title.data
        app_obj.main_title    = form.main_title.data
        app_obj.url           = form.url.data.strip()
        app_obj.endpoint      = form.endpoint.data.strip().lower().replace(" ", "_")
        app_obj.description   = form.description.data or None
        app_obj.icon          = form.icon.data
        app_obj.color_theme   = form.color_theme.data or None
        app_obj.is_active     = form.is_active.data
        app_obj.in_sidebar    = form.in_sidebar.data
        app_obj.require_login = form.require_login.data
        app_obj.api_enabled   = form.api_enabled.data
        app_obj.items_per_page = form.items_per_page.data or 20
        app_obj.export_csv    = form.export_csv.data
        app_obj.export_excel  = form.export_excel.data
        app_obj.soft_delete   = form.soft_delete.data
        app_obj.audit_log     = form.audit_log.data
        current_user.log_activity("app_updated", module="app_manager", payload={"app": app_obj.name})
        db.session.commit()
        # Re-register routes with updated name/url
        if app_obj.is_active:
            from arasCore.arasAdmin.services import _register_built_app, clear_cache
            clear_cache(app_obj.name)
            ok = _register_built_app(app_obj.id, current_app._get_current_object())
            if ok:
                flash(f"App '{app_obj.name}' updated and routes re-registered. Restart server if old routes still appear.", "success")
            else:
                flash(f"App '{app_obj.name}' updated. Route re-registration failed — restart server to apply.", "warning")
        else:
            flash(f"App '{app_obj.name}' updated.", "success")
        return redirect(url_for("admin.apps"))
    return render_template(
        "admin/app_form.html",
        title=f"Edit — {app_obj.name}",
        main_title=f"Edit App: {app_obj.name}",
        form=form,
        app=app_obj,
    )


# ── App Manager — activate / deactivate / delete / fields ────────────────────

@arasAdmin_bp.route("/apps/<int:app_id>/activate", methods=["POST"])
@login_required
def apps_activate(app_id):
    from .models import AppManagerApp
    app_obj = AppManagerApp.query.get_or_404(app_id)
    app_obj.is_active = True
    db.session.commit()
    # Attempt live registration
    from arasCore.arasAdmin.services import _register_built_app, clear_cache
    from arasCore.arasAdmin.models import AppManagerTable
    clear_cache(app_obj.name)
    ok = _register_built_app(app_obj.id, current_app._get_current_object())
    # Seed RBAC permissions for this app's tables
    try:
        from arasCore.rbac import seed_app_permissions
        resource_slugs = [t.name for t in AppManagerTable.query.filter_by(app_id=app_obj.id, is_active=True).all()]
        if resource_slugs:
            seed_app_permissions(app_obj.name, resource_slugs, db)
    except Exception as _re:
        current_app.logger.warning(f"[routes] RBAC seed failed on activate for {app_obj.name}: {_re}")
    if ok:
        flash(f"App '{app_obj.title}' activated and routes registered.", "success")
    else:
        flash(f"App saved as active but route registration failed. Restart server.", "warning")
    return redirect(url_for("admin.apps"))


@arasAdmin_bp.route("/apps/<int:app_id>/deactivate", methods=["POST"])
@login_required
def apps_deactivate(app_id):
    from .models import AppManagerApp
    from arasCore.arasAdmin.services import clear_cache
    app_obj = AppManagerApp.query.get_or_404(app_id)
    app_obj.is_active = False
    db.session.commit()
    clear_cache(app_obj.name)
    flash(f"App '{app_obj.title}' deactivated. Restart server for full effect.", "info")
    return redirect(url_for("admin.apps"))


@arasAdmin_bp.route("/apps/<int:app_id>/delete", methods=["POST"])
@login_required
def apps_delete(app_id):
    from .models import AppManagerApp, AppManagerField
    from arasCore.arasAdmin.services import clear_cache
    app_obj = AppManagerApp.query.get_or_404(app_id)
    name = app_obj.title
    app_slug = app_obj.name
    clear_cache(app_slug)
    current_user.log_activity("app_deleted", module="app_manager", payload={"app": name})
    AppManagerField.query.filter_by(app_id=app_id).delete()
    db.session.delete(app_obj)
    db.session.commit()
    # Remove RBAC permissions for the deleted app
    try:
        from arasCore.rbac import unseed_app_permissions
        unseed_app_permissions(app_slug, db)
    except Exception as _re:
        current_app.logger.warning(f"[routes] RBAC unseed failed for {app_slug}: {_re}")
    flash(f"App '{name}' deleted.", "danger")
    return redirect(url_for("admin.apps"))


# ── App Manager — tables ──────────────────────────────────────────────────────

@arasAdmin_bp.route("/apps/<int:app_id>/tables")
@login_required
def apps_tables(app_id):
    from .models import AppManagerApp, AppManagerTable
    app_obj = AppManagerApp.query.get_or_404(app_id)
    tables  = AppManagerTable.query.filter_by(app_id=app_id).order_by(AppManagerTable.menu_order).all()
    return render_template(
        "admin/ab_tables.html",
        title=f"Tables — {app_obj.title}",
        main_title=app_obj.main_title,
        app_def=app_obj,
        tables=tables,
    )


@arasAdmin_bp.route("/apps/<int:app_id>/tables/new", methods=["GET", "POST"])
@login_required
def apps_table_new(app_id):
    from .models import AppManagerApp, AppManagerTable
    from .forms import AppManagerTableForm
    app_obj = AppManagerApp.query.get_or_404(app_id)
    form    = AppManagerTableForm(app_id=app_id)
    if form.validate_on_submit():
        parent_id = form.parent_table_id.data or None
        tbl = AppManagerTable(
            app_id          = app_obj.id,
            parent_table_id = parent_id if parent_id else None,
            name            = form.name.data.strip().lower().replace(" ", "_"),
            title           = form.title.data,
            url_suffix      = form.url_suffix.data.strip(),
            menu_title      = form.menu_title.data or None,
            menu_icon       = form.menu_icon.data,
            show_in_menu    = form.show_in_menu.data,
            menu_order      = form.menu_order.data or 0,
            is_active       = form.is_active.data,
            search_enabled  = form.search_enabled.data,
            sort_field      = form.sort_field.data or None,
            sort_direction  = form.sort_direction.data,
            list_columns    = form.list_columns.data or None,
            per_page        = form.per_page.data or 20,
            allow_create    = form.allow_create.data,
            allow_edit      = form.allow_edit.data,
            allow_delete    = form.allow_delete.data,
            detail_view     = form.detail_view.data,
        )
        db.session.add(tbl)
        db.session.commit()
        flash(f"Table '{tbl.title}' created. Add columns now.", "success")
        return redirect(url_for("admin.apps_columns", app_id=app_id, table_id=tbl.id))
    return render_template(
        "admin/ab_table_form.html",
        title="New Table",
        main_title=app_obj.main_title,
        app_def=app_obj,
        form=form,
    )


@arasAdmin_bp.route("/apps/<int:app_id>/tables/<int:table_id>/edit", methods=["GET", "POST"])
@login_required
def apps_table_edit(app_id, table_id):
    from .models import AppManagerApp, AppManagerTable
    from .forms import AppManagerTableForm
    app_obj = AppManagerApp.query.get_or_404(app_id)
    tbl     = AppManagerTable.query.get_or_404(table_id)
    form    = AppManagerTableForm(app_id=app_id, obj=tbl)
    if form.validate_on_submit():
        tbl.name            = form.name.data.strip().lower().replace(" ", "_")
        tbl.title           = form.title.data
        tbl.url_suffix      = form.url_suffix.data.strip()
        tbl.menu_title      = form.menu_title.data or None
        tbl.menu_icon       = form.menu_icon.data
        tbl.show_in_menu    = form.show_in_menu.data
        tbl.menu_order      = form.menu_order.data or 0
        tbl.is_active       = form.is_active.data
        pid = form.parent_table_id.data
        tbl.parent_table_id  = pid if pid else None
        tbl.search_enabled   = form.search_enabled.data
        tbl.sort_field       = form.sort_field.data or None
        tbl.sort_direction   = form.sort_direction.data
        tbl.list_columns     = form.list_columns.data or None
        tbl.per_page         = form.per_page.data or 20
        tbl.allow_create     = form.allow_create.data
        tbl.allow_edit       = form.allow_edit.data
        tbl.allow_delete     = form.allow_delete.data
        tbl.detail_view      = form.detail_view.data
        db.session.commit()
        from arasCore.arasAdmin.services import clear_cache
        clear_cache(app_obj.name)
        flash(f"Table '{tbl.title}' updated.", "success")
        return redirect(url_for("admin.apps_tables", app_id=app_id))
    return render_template(
        "admin/ab_table_form.html",
        title=f"Edit Table — {tbl.title}",
        main_title=app_obj.main_title,
        app_def=app_obj,
        form=form,
        tbl=tbl,
    )


@arasAdmin_bp.route("/apps/<int:app_id>/tables/<int:table_id>/delete", methods=["POST"])
@login_required
def apps_table_delete(app_id, table_id):
    from .models import AppManagerTable, AppManagerApp
    from arasCore.arasAdmin.services import clear_cache
    tbl     = AppManagerTable.query.get_or_404(table_id)
    app_obj = AppManagerApp.query.get_or_404(app_id)
    title   = tbl.title
    db.session.delete(tbl)
    db.session.commit()
    clear_cache(app_obj.name)
    flash(f"Table '{title}' deleted.", "danger")
    return redirect(url_for("admin.apps_tables", app_id=app_id))


# ── App Manager — columns ─────────────────────────────────────────────────────

@arasAdmin_bp.route("/apps/<int:app_id>/tables/<int:table_id>/columns", methods=["GET", "POST"])
@login_required
def apps_columns(app_id, table_id):
    from .models import AppManagerApp, AppManagerTable, AppManagerColumn
    from .forms import AppManagerColumnForm
    from arasCore.arasAdmin.services import clear_cache
    app_obj = AppManagerApp.query.get_or_404(app_id)
    tbl     = AppManagerTable.query.get_or_404(table_id)
    form    = AppManagerColumnForm(app_id=app_id)
    if form.validate_on_submit():
        rel_tid = form.relation_table_id.data or None
        col = AppManagerColumn(
            table_id              = tbl.id,
            name                  = form.name.data.strip().lower().replace(" ", "_"),
            label                 = form.label.data,
            field_type            = form.field_type.data,
            length                = form.length.data or None,
            required              = form.required.data,
            default_value         = form.default_value.data or None,
            order                 = form.order.data or 0,
            placeholder           = form.placeholder.data or None,
            help_text             = form.help_text.data or None,
            show_in_list          = form.show_in_list.data,
            show_in_form          = form.show_in_form.data,
            readonly              = form.readonly.data,
            min_value             = form.min_value.data or None,
            max_value             = form.max_value.data or None,
            max_length            = form.max_length.data or None,
            unique                = form.unique.data,
            searchable            = form.searchable.data,
            choices               = form.choices.data or None,
            relation_table_id     = rel_tid if rel_tid else None,
            relation_system_table = form.relation_system_table.data or None,
            relation_display_col  = form.relation_display_col.data or None,
            cascade_delete        = form.cascade_delete.data,
        )
        db.session.add(col)
        db.session.commit()
        clear_cache(app_obj.name)
        from arasCore.arasAdmin.services import make_table_model, sync_table_columns
        new_model = make_table_model(tbl, app_obj.name, AppManagerTable.query.filter_by(app_id=app_id).all())
        sync_table_columns(new_model)
        flash(f"Column '{col.label}' added.", "success")
        return redirect(url_for("admin.apps_columns", app_id=app_id, table_id=table_id))

    columns = AppManagerColumn.query.filter_by(table_id=table_id).order_by(AppManagerColumn.order).all()
    all_tables = AppManagerTable.query.filter_by(app_id=app_id).all()
    return render_template(
        "admin/ab_columns.html",
        title=f"Columns — {tbl.title}",
        main_title=app_obj.main_title,
        app_def=app_obj,
        tbl=tbl,
        columns=columns,
        form=form,
        all_tables=all_tables,
    )


@arasAdmin_bp.route("/apps/<int:app_id>/tables/<int:table_id>/columns/<int:col_id>/delete", methods=["POST"])
@login_required
def apps_column_delete(app_id, table_id, col_id):
    from .models import AppManagerColumn, AppManagerApp
    from arasCore.arasAdmin.services import clear_cache
    col     = AppManagerColumn.query.get_or_404(col_id)
    app_obj = AppManagerApp.query.get_or_404(app_id)
    label   = col.label
    db.session.delete(col)
    db.session.commit()
    clear_cache(app_obj.name)
    flash(f"Column '{label}' deleted.", "warning")
    return redirect(url_for("admin.apps_columns", app_id=app_id, table_id=table_id))


@arasAdmin_bp.route("/apps/<int:app_id>/tables/<int:table_id>/columns/<int:col_id>/edit", methods=["POST"])
@login_required
def apps_column_edit(app_id, table_id, col_id):
    from .models import AppManagerColumn, AppManagerApp
    from arasCore.arasAdmin.services import clear_cache
    col     = AppManagerColumn.query.get_or_404(col_id)
    app_obj = AppManagerApp.query.get_or_404(app_id)
    col.name          = request.form.get("name", col.name).strip().lower().replace(" ", "_")
    col.label         = request.form.get("label", col.label)
    col.field_type    = request.form.get("field_type", col.field_type)
    col.order         = int(request.form.get("order") or col.order)
    col.required      = request.form.get("required") == "y"
    col.default_value = request.form.get("default_value") or None
    col.placeholder   = request.form.get("placeholder") or None
    col.help_text     = request.form.get("help_text") or None
    col.show_in_list  = request.form.get("show_in_list") == "y"
    col.show_in_form  = request.form.get("show_in_form") == "y"
    col.readonly      = request.form.get("readonly") == "y"
    col.unique        = request.form.get("unique") == "y"
    col.searchable    = request.form.get("searchable") == "y"
    col.choices       = request.form.get("choices") or None
    col.length        = int(request.form.get("length")) if request.form.get("length") else None
    col.max_length    = int(request.form.get("max_length")) if request.form.get("max_length") else None
    col.min_value     = request.form.get("min_value") or None
    col.max_value     = request.form.get("max_value") or None
    db.session.commit()
    clear_cache(app_obj.name)
    flash(f"Column '{col.label}' updated.", "success")
    return redirect(url_for("admin.apps_columns", app_id=app_id, table_id=table_id))


# backward compat redirect
@arasAdmin_bp.route("/apps/<int:app_id>/fields")
@login_required
def apps_fields(app_id):
    return redirect(url_for("admin.apps_tables", app_id=app_id))


@arasAdmin_bp.route("/apps/<int:app_id>/fields/<int:field_id>/delete", methods=["POST"])
@login_required
def apps_field_delete(app_id, field_id):
    return redirect(url_for("admin.apps_tables", app_id=app_id))


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
    return redirect(url_for("admin.settings") + "#panel-roles")


@arasAdmin_bp.route("/roles/<int:role_id>/delete", methods=["POST"])
@login_required
def role_delete(role_id):
    from arasCore.permissions import Role
    role = Role.query.get_or_404(role_id)
    db.session.delete(role)
    db.session.commit()
    flash(f"Role '{role.name}' deleted.", "warning")
    return redirect(url_for("admin.settings") + "#panel-roles")


@arasAdmin_bp.route("/roles/<int:role_id>/toggle", methods=["POST"])
@login_required
def role_toggle(role_id):
    from arasCore.permissions import Role
    role = Role.query.get_or_404(role_id)
    role.is_active = not role.is_active
    db.session.commit()
    return redirect(url_for("admin.settings") + "#panel-roles")


@arasAdmin_bp.route("/roles/<int:role_id>/permissions", methods=["POST"])
@login_required
def role_permissions_save(role_id):
    from arasCore.permissions import Role, Permission
    role = Role.query.get_or_404(role_id)
    perm_ids = [int(x) for x in request.form.getlist("perm_ids")]
    role.permissions = Permission.query.filter(Permission.id.in_(perm_ids)).all()
    db.session.commit()
    flash("Permissions updated.", "success")
    return redirect(url_for("admin.settings") + "#panel-roles")


@arasAdmin_bp.route("/roles/<int:role_id>/users", methods=["POST"])
@login_required
def role_users_save(role_id):
    from arasCore.permissions import Role, UserRole
    role = Role.query.get_or_404(role_id)
    user_ids = [int(x) for x in request.form.getlist("user_ids")]
    app_slug = request.form.get("app_slug") or None
    UserRole.query.filter_by(role_id=role_id, app_slug=app_slug).delete()
    for uid in user_ids:
        db.session.add(UserRole(user_id=uid, role_id=role_id, app_slug=app_slug))
    db.session.commit()
    flash("User assignments updated.", "success")
    return redirect(url_for("admin.settings") + "#panel-roles")


# ── Users list ───────────────────────────────────────────────────────────────

@arasAdmin_bp.route("/users")
@login_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template(
        "admin/users.html",
        title="Users",
        main_title="All Users",
        users=all_users,
    )


@arasAdmin_bp.route("/users/new", methods=["GET", "POST"])
@login_required
def users_new():
    from arasCore.auth import create_user
    form = CreateUserForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered.", "warning")
        elif User.query.filter_by(username=form.username.data).first():
            flash("Username already taken.", "warning")
        else:
            u = create_user(form.username.data, form.email.data, form.password.data, is_admin=form.is_admin.data)
            current_user.log_activity("user_created", module="users", payload={"target": u.username})
            db.session.commit()
            flash(f"User '{u.username}' created.", "success")
            return redirect(url_for("admin.users"))
    return render_template("admin/user_form.html", title="New User", main_title="Create User", form=form)


@arasAdmin_bp.route("/users/<int:user_id>/activate", methods=["POST"])
@login_required
def user_activate(user_id):
    u = User.query.get_or_404(user_id)
    u.is_active = True
    current_user.log_activity("user_activated", module="users", payload={"target": u.username})
    db.session.commit()
    flash(f"User '{u.username}' activated.", "success")
    return redirect(url_for("admin.users"))


@arasAdmin_bp.route("/users/<int:user_id>/deactivate", methods=["POST"])
@login_required
def user_deactivate(user_id):
    if user_id == current_user.id:
        flash("Cannot deactivate yourself.", "warning")
        return redirect(url_for("admin.users"))
    u = User.query.get_or_404(user_id)
    u.is_active = False
    current_user.log_activity("user_deactivated", module="users", payload={"target": u.username})
    db.session.commit()
    flash(f"User '{u.username}' deactivated.", "info")
    return redirect(url_for("admin.users"))


@arasAdmin_bp.route("/users/<int:user_id>/toggle-admin", methods=["POST"])
@login_required
def user_toggle_admin(user_id):
    if user_id == current_user.id:
        flash("Cannot change your own admin status.", "warning")
        return redirect(url_for("admin.users"))
    u = User.query.get_or_404(user_id)
    u.is_admin = not u.is_admin
    status = "granted" if u.is_admin else "revoked"
    current_user.log_activity(f"admin_{status}", module="users", payload={"target": u.username})
    db.session.commit()
    flash(f"Admin {status} for '{u.username}'.", "success")
    return redirect(url_for("admin.users"))


@arasAdmin_bp.route("/users/export-csv")
@login_required
def users_export_csv():
    import csv, io
    all_users = User.query.order_by(User.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "username", "email", "is_admin", "is_active", "created_at"])
    for u in all_users:
        writer.writerow([u.id, u.username, u.email, u.is_admin, u.is_active,
                         u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else ""])
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=users.csv"},
    )


# ── Post / Explore ────────────────────────────────────────────────────────────

# @arasAdmin_bp.route("/post", methods=["GET", "POST"])
# @login_required
# def post():
#     form = PostForm()
#     if form.validate_on_submit():
#         p = Post(body=form.post.data, user_id=current_user.id)
#         db.session.add(p)
#         db.session.commit()
#         flash("Your post is now live!", "success")
#         return redirect(url_for("admin.post"))

#     per_pg = current_app.config.get("POSTS_PER_PAGE", 10)
#     page   = request.args.get("page", 1, type=int)
#     posts  = (
#         Post.query
#         .filter_by(user_id=current_user.id)
#         .order_by(Post.timestamp.desc())
#         .paginate(page=page, per_page=per_pg, error_out=False)
#     )
#     next_url = url_for("admin.post", page=posts.next_num) if posts.has_next else None
#     prev_url = url_for("admin.post", page=posts.prev_num) if posts.has_prev else None
#     return render_template(
#         "admin/adm_index.html",
#         main_title="Post",
#         title="Post",
#         form=form,
#         posts=posts.items,
#         next_url=next_url,
#         prev_url=prev_url,
#     )


# @arasAdmin_bp.route("/explore")
# @login_required
# def explore():
#     per_pg = current_app.config.get("POSTS_PER_PAGE", 10)
#     page   = request.args.get("page", 1, type=int)
#     posts  = Post.query.order_by(Post.timestamp.desc()).paginate(page=page, per_page=per_pg, error_out=False)
#     next_url = url_for("admin.explore", page=posts.next_num) if posts.has_next else None
#     prev_url = url_for("admin.explore", page=posts.prev_num) if posts.has_prev else None
#     return render_template(
#         "admin/adm_index.html",
#         title="Explore",
#         main_title="Explore",
#         posts=posts.items,
#         next_url=next_url,
#         prev_url=prev_url,
#     )


# ── App Installer ─────────────────────────────────────────────────────────────

@arasAdmin_bp.route("/apps/install", methods=["GET", "POST"])
@login_required
def apps_install():
    """Install app from YAML/JSON definition or Python zip upload."""
    if request.method == "POST":
        install_type = request.form.get("install_type", "definition")

        if install_type == "python":
            # Python zip upload → PythonLoaderMiddleware
            f = request.files.get("python_file")
            if not f or not f.filename:
                flash("No zip file selected.", "warning")
                return redirect(url_for("admin.apps_install"))
            if not f.filename.lower().endswith(".zip"):
                flash("Only .zip files accepted for Python install.", "danger")
                return redirect(url_for("admin.apps_install"))
            try:
                from arasCore.lib.middleware import PythonLoaderMiddleware
                result = PythonLoaderMiddleware.from_zip(f, current_app._get_current_object())
                flash(result["message"], "success" if result["registered"] else "info")
                return redirect(url_for("admin.apps"))
            except ValueError as e:
                flash(str(e), "danger")
            except Exception as e:
                current_app.logger.error(f"Python install error: {e}", exc_info=True)
                flash(f"Install failed: {e}", "danger")

        else:
            # YAML/JSON definition → AppDefinitionMiddleware → installer
            f = request.files.get("definition_file")
            if not f or not f.filename:
                flash("No file selected.", "warning")
                return redirect(url_for("admin.apps_install"))
            try:
                from arasCore.lib.installer import load_definition_from_file, install_from_definition
                definition = load_definition_from_file(f)
                app_obj    = install_from_definition(definition, db, current_app._get_current_object())
                flash(
                    f"App '{app_obj.name}' installed. Add tables/columns and activate when ready.",
                    "success",
                )
                return redirect(url_for("admin.apps_tables", app_id=app_obj.id))
            except ValueError as e:
                flash(str(e), "danger")
            except Exception as e:
                current_app.logger.error(f"Install error: {e}", exc_info=True)
                flash(f"Install failed: {e}", "danger")

    return render_template(
        "admin/app_install.html",
        title="Install App",
        main_title="Install App",
    )


@arasAdmin_bp.route("/apps/install-manifest/<app_name>", methods=["POST"])
@login_required
def apps_install_manifest(app_name):
    """Sync a code-based app (Python manifest/AppHelper) into mgr_app/mgr_table/mgr_column."""
    import importlib
    from arasCore.lib.installer import sync_helper_to_db
    from arasCore.lib.app_helper import AppHelper

    app_slug = app_name[len("app_"):] if app_name.startswith("app_") else app_name
    pkg_name = f"aras.app_{app_slug}"

    try:
        mod = importlib.import_module(f"{pkg_name}.manifest")
        helper = getattr(mod, "helper", None)
    except ModuleNotFoundError:
        flash(f"No manifest found for '{pkg_name}'.", "danger")
        return redirect(url_for("admin.apps"))

    if not isinstance(helper, AppHelper):
        flash(f"'{pkg_name}.manifest' has no AppHelper instance.", "danger")
        return redirect(url_for("admin.apps"))

    try:
        app_obj, stats = sync_helper_to_db(helper, db, current_app._get_current_object())
        flash(
            f"Synced '{app_obj.name}': {stats['tables_new']} new tables, "
            f"{stats['cols_new']} new columns.",
            "success",
        )
        return redirect(url_for("admin.apps_tables", app_id=app_obj.id))
    except Exception as e:
        current_app.logger.error(f"install-manifest error: {e}", exc_info=True)
        flash(f"Sync failed: {e}", "danger")
        return redirect(url_for("admin.apps"))


@arasAdmin_bp.route("/apps/<int:app_id>/sync", methods=["POST"])
@login_required
def apps_sync(app_id):
    """Re-sync a code-based app: diff SA model vs mgr_column, insert new columns."""
    import importlib
    from arasCore.lib.installer import sync_helper_to_db
    from arasCore.lib.app_helper import AppHelper
    from arasCore.arasAdmin.models import AppManagerApp

    app_obj = AppManagerApp.query.get_or_404(app_id)

    # Try helper_registry first, then import manifest directly
    from arasCore.lib.blueprints import get_helper_registry
    helper = get_helper_registry().get(app_obj.name)

    if helper is None:
        pkg_name = f"aras.app_{app_obj.name}"
        try:
            mod = importlib.import_module(f"{pkg_name}.manifest")
            helper = getattr(mod, "helper", None)
        except ModuleNotFoundError:
            flash(f"No Python manifest found for '{app_obj.name}'.", "warning")
            return redirect(url_for("admin.apps_tables", app_id=app_id))

    if not isinstance(helper, AppHelper):
        flash("App has no AppHelper manifest — nothing to sync.", "warning")
        return redirect(url_for("admin.apps_tables", app_id=app_id))

    try:
        _, stats = sync_helper_to_db(helper, db, current_app._get_current_object())
        flash(
            f"Sync complete: {stats['tables_new']} new tables, {stats['cols_new']} new columns "
            f"({stats['cols_skipped']} already existed).",
            "success",
        )
    except Exception as e:
        current_app.logger.error(f"sync error: {e}", exc_info=True)
        flash(f"Sync failed: {e}", "danger")

    return redirect(url_for("admin.apps_tables", app_id=app_id))


@arasAdmin_bp.route("/apps/template/yaml")
@login_required
def apps_template_yaml():
    """Download YAML app definition template."""
    from flask import Response
    from arasCore.lib.installer import generate_yaml_template
    content = generate_yaml_template()
    return Response(
        content,
        mimetype="text/yaml",
        headers={"Content-Disposition": "attachment;filename=aras_app_template.yaml"},
    )


@arasAdmin_bp.route("/apps/template/json")
@login_required
def apps_template_json():
    """Download JSON app definition template."""
    from flask import Response
    from arasCore.lib.installer import generate_json_template
    content = generate_json_template()
    return Response(
        content,
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=aras_app_template.json"},
    )


@arasAdmin_bp.route("/apps/<int:app_id>/export/yaml")
@login_required
def apps_export_yaml(app_id):
    """Export an existing app as YAML definition."""
    import yaml
    from flask import Response
    from .models import AppManagerApp
    app_obj = AppManagerApp.query.get_or_404(app_id)
    definition = _build_export_definition(app_obj)
    content = yaml.dump(definition, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return Response(
        content.encode("utf-8"),
        mimetype="text/yaml",
        headers={"Content-Disposition": f"attachment;filename={app_obj.name}.yaml"},
    )


@arasAdmin_bp.route("/apps/<int:app_id>/export/json")
@login_required
def apps_export_json(app_id):
    """Export an existing app as JSON definition."""
    import json
    from flask import Response
    from .models import AppManagerApp
    app_obj = AppManagerApp.query.get_or_404(app_id)
    definition = _build_export_definition(app_obj)
    content = json.dumps(definition, indent=2, ensure_ascii=False)
    return Response(
        content.encode("utf-8"),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment;filename={app_obj.name}.json"},
    )


def _build_export_definition(app_obj) -> dict:
    """Serialize AppManagerApp → definition dict (mirrors installer format)."""
    from .models import AppManagerTable, AppManagerColumn
    tables = AppManagerTable.query.filter_by(app_id=app_obj.id).order_by(AppManagerTable.menu_order).all()
    tables_out = []
    for tbl in tables:
        cols = AppManagerColumn.query.filter_by(table_id=tbl.id).order_by(AppManagerColumn.order).all()
        tables_out.append({
            "name":           tbl.name,
            "title":          tbl.title,
            "url_suffix":     tbl.url_suffix,
            "menu_title":     tbl.menu_title or tbl.title,
            "menu_icon":      tbl.menu_icon,
            "show_in_menu":   tbl.show_in_menu,
            "menu_order":     tbl.menu_order,
            "is_active":      tbl.is_active,
            "allow_create":   tbl.allow_create,
            "allow_edit":     tbl.allow_edit,
            "allow_delete":   tbl.allow_delete,
            "detail_view":    tbl.detail_view,
            "search_enabled": tbl.search_enabled,
            "sort_field":     tbl.sort_field,
            "sort_direction": tbl.sort_direction,
            "columns": [
                {
                    "name":       c.name,
                    "label":      c.label,
                    "field_type": c.field_type,
                    "required":   c.required,
                    "order":      c.order,
                    "show_in_list": c.show_in_list,
                    "show_in_form": c.show_in_form,
                    "readonly":   c.readonly,
                    "unique":     c.unique,
                    "searchable": c.searchable,
                    "placeholder":  c.placeholder,
                    "help_text":    c.help_text,
                    "default_value": c.default_value,
                    "max_length":   c.max_length,
                    "choices":      c.choices,
                    "relation_system_table": c.relation_system_table,
                    "relation_display_col":  c.relation_display_col,
                }
                for c in cols
            ],
        })
    return {
        "app": {
            "name":          app_obj.name,
            "title":         app_obj.title,
            "main_title":    app_obj.main_title,
            "url":           app_obj.url,
            "endpoint":      app_obj.endpoint,
            "description":   app_obj.description,
            "icon":          app_obj.icon,
            "is_active":     app_obj.is_active,
            "in_sidebar":    app_obj.in_sidebar,
            "require_login": app_obj.require_login,
            "api_enabled":   app_obj.api_enabled,
            "items_per_page": app_obj.items_per_page,
            "export_csv":    app_obj.export_csv,
            "export_excel":  app_obj.export_excel,
            "soft_delete":   app_obj.soft_delete,
            "audit_log":     app_obj.audit_log,
            "menu_order":    app_obj.menu_order,
        },
        "tables": tables_out,
    }
