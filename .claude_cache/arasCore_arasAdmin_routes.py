# -*- coding: utf-8 -*-
"""arasCore/arasAdmin/routes.py — Admin routes (migrated from app_admin/routes.py)."""
from datetime import datetime

from flask import render_template, request, jsonify, redirect, url_for, flash, g, current_app
from flask_login import login_required, current_user

from . import arasAdmin_bp
from .models import Message, Notification, UserActivity, Post
from .forms import MessageForm, PostForm, AppBuilderAppForm
from .services import get_dashboard_widgets, build_sidebar_menu
from arasCore.lib.extensions import db
from arasCore.auth import User


# ── Before request ────────────────────────────────────────────────────────────

@arasAdmin_bp.before_app_request
def before_request():
    g.user = current_user
    if current_user.is_authenticated:
        g.messages   = current_user.messages_received.order_by(Message.timestamp.desc())
        g.activities = current_user.activities.order_by(UserActivity.created_at.desc())
        g.gmenu = build_sidebar_menu()


# ── Dashboard ─────────────────────────────────────────────────────────────────

@arasAdmin_bp.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        flash("Your post is now live!", "success")
        return redirect(url_for("admin.dashboard"))

    page   = request.args.get("page", 1, type=int)
    per_pg = current_app.config.get("POSTS_PER_PAGE", 10)
    posts  = Post.query.order_by(Post.timestamp.desc()).paginate(page=page, per_page=per_pg, error_out=False)

    next_url = url_for("admin.dashboard", page=posts.next_num) if posts.has_next else None
    prev_url = url_for("admin.dashboard", page=posts.prev_num) if posts.has_prev else None

    widgets = get_dashboard_widgets(current_user)

    return render_template(
        "admin/dashboard.html",
        title="Dashboard",
        main_title="Admin Dashboard",
        form=form,
        posts=posts.items,
        post=posts,
        user=current_user,
        next_url=next_url,
        prev_url=prev_url,
        widgets=widgets,
    )


# ── Dev page ──────────────────────────────────────────────────────────────────

@arasAdmin_bp.route("/dev")
def dev():
    return render_template("admin/dev.html", main_title="Dev Page", user=current_user)


# ── Messages ──────────────────────────────────────────────────────────────────

@arasAdmin_bp.route("/send_message/<recipient>", methods=["GET", "POST"])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(sender_id=current_user.id, recipient_id=user.id, body=form.message.data)
        db.session.add(msg)
        user.add_notification("unread_message_count", user.new_messages(), category="message")
        db.session.commit()
        flash("Your message has been sent.", "success")
        return redirect(url_for("admin.messages"))
    return render_template(
        "admin/send_message.html",
        title="Send Message",
        main_title="Message",
        form=form,
        recipient=recipient,
    )


@arasAdmin_bp.route("/messages")
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification("unread_message_count", 0, category="message")
    db.session.commit()

    per_pg   = current_app.config.get("POSTS_PER_PAGE", 10)
    page     = request.args.get("page", 1, type=int)
    messages = current_user.messages_received.order_by(Message.timestamp.desc()).paginate(
        page=page, per_page=per_pg, error_out=False
    )
    next_url = url_for("admin.messages", page=messages.next_num) if messages.has_next else None
    prev_url = url_for("admin.messages", page=messages.prev_num) if messages.has_prev else None

    return render_template(
        "admin/messages.html",
        title="Messages",
        main_title="Messages",
        messages=messages.items,
        next_url=next_url,
        prev_url=prev_url,
    )


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


# ── Activities ────────────────────────────────────────────────────────────────

@arasAdmin_bp.route("/activities", methods=["GET", "POST"])
@login_required
def activities():
    current_user.last_activity_read_time = datetime.utcnow()
    current_user.add_notification("unread_activity_count", 0, category="activity")
    db.session.commit()
    activities = current_user.activities.order_by(UserActivity.created_at.desc()).all()
    return render_template(
        "admin/activities.html",
        title="Activities",
        main_title="Activities",
        activities=activities,
    )


# ── Settings ─────────────────────────────────────────────────────────────────

@arasAdmin_bp.route("/settings")
@login_required
def settings():
    from .models import AppBuilderApp
    from arasCore.lib.extensions import db
    from sqlalchemy import inspect as sa_inspect

    all_apps  = AppBuilderApp.query.order_by(AppBuilderApp.id).all()
    all_users = User.query.order_by(User.created_at.desc()).all()

    # DB info
    db_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
    # Mask password in URI
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

    return render_template(
        "admin/settings.html",
        title="Settings",
        main_title="Settings",
        apps=all_apps,
        users=all_users,
        db_uri=db_uri_display,
        db_tables=db_tables,
    )


@arasAdmin_bp.route("/settings/db/generate-view", methods=["POST"])
@login_required
def db_generate_view():
    """Generate an AppBuilderApp entry from an existing table."""
    from .models import AppBuilderApp
    table_name = request.form.get("table_name", "").strip()
    if not table_name:
        flash("No table selected.", "warning")
        return redirect(url_for("admin.settings") + "#panel-database")

    # Check if already exists
    existing = AppBuilderApp.query.filter_by(name=table_name).first()
    if existing:
        flash(f"App for table '{table_name}' already exists.", "info")
        return redirect(url_for("admin.settings") + "#panel-database")

    slug  = table_name.replace("-", "_")
    title = slug.replace("_", " ").title()
    app_obj = AppBuilderApp(
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


# ── Apps (App Manager) ────────────────────────────────────────────────────────

@arasAdmin_bp.route("/apps")
@login_required
def apps():
    from .models import AppBuilderApp
    all_apps = AppBuilderApp.query.order_by(AppBuilderApp.id).all()
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
    from .models import AppBuilderApp
    form = AppBuilderAppForm()
    if form.validate_on_submit():
        app_obj = AppBuilderApp(
            name=form.name.data.strip().lower().replace(" ", "_"),
            title=form.title.data,
            main_title=form.main_title.data,
            url=form.url.data.strip(),
            endpoint=form.endpoint.data.strip().lower().replace(" ", "_"),
            is_active=form.is_active.data,
            in_sidebar=form.in_sidebar.data,
        )
        db.session.add(app_obj)
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
    from .models import AppBuilderApp
    app_obj = AppBuilderApp.query.get_or_404(app_id)
    form = AppBuilderAppForm(obj=app_obj)
    if form.validate_on_submit():
        app_obj.name       = form.name.data.strip().lower().replace(" ", "_")
        app_obj.title      = form.title.data
        app_obj.main_title = form.main_title.data
        app_obj.url        = form.url.data.strip()
        app_obj.endpoint   = form.endpoint.data.strip().lower().replace(" ", "_")
        app_obj.is_active  = form.is_active.data
        app_obj.in_sidebar = form.in_sidebar.data
        db.session.commit()
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
    from .models import AppBuilderApp
    app_obj = AppBuilderApp.query.get_or_404(app_id)
    app_obj.is_active = True
    db.session.commit()
    # Attempt live registration
    from arasCore.arasAdmin.services import _register_built_app, clear_cache
    clear_cache(app_obj.name)
    ok = _register_built_app(app_obj.id, current_app._get_current_object())
    if ok:
        flash(f"App '{app_obj.title}' activated and routes registered.", "success")
    else:
        flash(f"App saved as active but route registration failed. Restart server.", "warning")
    return redirect(url_for("admin.apps"))


@arasAdmin_bp.route("/apps/<int:app_id>/deactivate", methods=["POST"])
@login_required
def apps_deactivate(app_id):
    from .models import AppBuilderApp
    from arasCore.arasAdmin.services import clear_cache
    app_obj = AppBuilderApp.query.get_or_404(app_id)
    app_obj.is_active = False
    db.session.commit()
    clear_cache(app_obj.name)
    flash(f"App '{app_obj.title}' deactivated. Restart server for full effect.", "info")
    return redirect(url_for("admin.apps"))


@arasAdmin_bp.route("/apps/<int:app_id>/delete", methods=["POST"])
@login_required
def apps_delete(app_id):
    from .models import AppBuilderApp, AppBuilderField
    from arasCore.arasAdmin.services import clear_cache
    app_obj = AppBuilderApp.query.get_or_404(app_id)
    name = app_obj.title
    clear_cache(app_obj.name)
    # Delete fields first (cascade should handle it, but explicit is safer)
    AppBuilderField.query.filter_by(app_id=app_id).delete()
    db.session.delete(app_obj)
    db.session.commit()
    flash(f"App '{name}' deleted.", "danger")
    return redirect(url_for("admin.apps"))


# ── App Manager — tables ──────────────────────────────────────────────────────

@arasAdmin_bp.route("/apps/<int:app_id>/tables")
@login_required
def apps_tables(app_id):
    from .models import AppBuilderApp, AppBuilderTable
    app_obj = AppBuilderApp.query.get_or_404(app_id)
    tables  = AppBuilderTable.query.filter_by(app_id=app_id).order_by(AppBuilderTable.menu_order).all()
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
    from .models import AppBuilderApp, AppBuilderTable
    from .forms import AppBuilderTableForm
    app_obj = AppBuilderApp.query.get_or_404(app_id)
    form    = AppBuilderTableForm(app_id=app_id)
    if form.validate_on_submit():
        parent_id = form.parent_table_id.data or None
        tbl = AppBuilderTable(
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
    from .models import AppBuilderApp, AppBuilderTable
    from .forms import AppBuilderTableForm
    app_obj = AppBuilderApp.query.get_or_404(app_id)
    tbl     = AppBuilderTable.query.get_or_404(table_id)
    form    = AppBuilderTableForm(app_id=app_id, obj=tbl)
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
        tbl.parent_table_id = pid if pid else None
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
    from .models import AppBuilderTable, AppBuilderApp
    from arasCore.arasAdmin.services import clear_cache
    tbl     = AppBuilderTable.query.get_or_404(table_id)
    app_obj = AppBuilderApp.query.get_or_404(app_id)
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
    from .models import AppBuilderApp, AppBuilderTable, AppBuilderColumn
    from .forms import AppBuilderColumnForm
    from arasCore.arasAdmin.services import clear_cache
    app_obj = AppBuilderApp.query.get_or_404(app_id)
    tbl     = AppBuilderTable.query.get_or_404(table_id)
    form    = AppBuilderColumnForm(app_id=app_id)
    if form.validate_on_submit():
        rel_tid = form.relation_table_id.data or None
        col = AppBuilderColumn(
            table_id              = tbl.id,
            name                  = form.name.data.strip().lower().replace(" ", "_"),
            label                 = form.label.data,
            field_type            = form.field_type.data,
            length                = form.length.data or None,
            required              = form.required.data,
            default_value         = form.default_value.data or None,
            order                 = form.order.data or 0,
            relation_table_id     = rel_tid if rel_tid else None,
            relation_system_table = form.relation_system_table.data or None,
            relation_display_col  = form.relation_display_col.data or None,
            cascade_delete        = form.cascade_delete.data,
        )
        db.session.add(col)
        db.session.commit()
        clear_cache(app_obj.name)
        flash(f"Column '{col.label}' added.", "success")
        return redirect(url_for("admin.apps_columns", app_id=app_id, table_id=table_id))

    columns = AppBuilderColumn.query.filter_by(table_id=table_id).order_by(AppBuilderColumn.order).all()
    all_tables = AppBuilderTable.query.filter_by(app_id=app_id).all()
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
    from .models import AppBuilderColumn, AppBuilderApp
    from arasCore.arasAdmin.services import clear_cache
    col     = AppBuilderColumn.query.get_or_404(col_id)
    app_obj = AppBuilderApp.query.get_or_404(app_id)
    label   = col.label
    db.session.delete(col)
    db.session.commit()
    clear_cache(app_obj.name)
    flash(f"Column '{label}' deleted.", "warning")
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


# ── Post / Explore ────────────────────────────────────────────────────────────

@arasAdmin_bp.route("/post", methods=["GET", "POST"])
@login_required
def post():
    form = PostForm()
    if form.validate_on_submit():
        p = Post(body=form.post.data, user_id=current_user.id)
        db.session.add(p)
        db.session.commit()
        flash("Your post is now live!", "success")
        return redirect(url_for("admin.post"))

    per_pg = current_app.config.get("POSTS_PER_PAGE", 10)
    page   = request.args.get("page", 1, type=int)
    posts  = (
        Post.query
        .filter_by(user_id=current_user.id)
        .order_by(Post.timestamp.desc())
        .paginate(page=page, per_page=per_pg, error_out=False)
    )
    next_url = url_for("admin.post", page=posts.next_num) if posts.has_next else None
    prev_url = url_for("admin.post", page=posts.prev_num) if posts.has_prev else None
    return render_template(
        "admin/adm_index.html",
        main_title="Post",
        title="Post",
        form=form,
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@arasAdmin_bp.route("/explore")
@login_required
def explore():
    per_pg = current_app.config.get("POSTS_PER_PAGE", 10)
    page   = request.args.get("page", 1, type=int)
    posts  = Post.query.order_by(Post.timestamp.desc()).paginate(page=page, per_page=per_pg, error_out=False)
    next_url = url_for("admin.explore", page=posts.next_num) if posts.has_next else None
    prev_url = url_for("admin.explore", page=posts.prev_num) if posts.has_prev else None
    return render_template(
        "admin/adm_index.html",
        title="Explore",
        main_title="Explore",
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
    )
