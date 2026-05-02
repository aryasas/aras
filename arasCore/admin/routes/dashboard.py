# -*- coding: utf-8 -*-
from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from arasCore.admin import admin_bp
from arasCore.admin.models import UserActivity, ArasSystemSetting, AppManagerDashboard
from arasCore.admin.services import get_dashboard_widgets
from arasCore.lib.core.extensions import db


@admin_bp.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    widgets = get_dashboard_widgets(current_user)
    builder_enabled = ArasSystemSetting.get("dashboard_builder_enabled", False)
    return render_template(
        "admin/base/base_dashboard.html",
        title="Dashboard",
        main_title="Admin Dashboard",
        user=current_user,
        widgets=widgets,
        builder_enabled=builder_enabled,
    )


@admin_bp.route("/dashboard/builder/add-widget", methods=["POST"])
@login_required
def dashboard_add_widget():
    if not ArasSystemSetting.get("dashboard_builder_enabled", False):
        return jsonify({"success": False, "error": "Builder disabled"}), 403
    
    data = request.json or {}
    app_id = data.get("app_id") # Can be null for global
    new_w = AppManagerDashboard(
        app_id=app_id,
        name=data.get("name", "New Widget"),
        label=data.get("label", "New Widget"),
        widget_type=data.get("widget_type", "count"),
        data_source=data.get("data_source", "auth_users"),
        config_json=data.get("config_json", "{}"),
        user_id=current_user.id,
        order=99,
    )
    db.session.add(new_w)
    db.session.commit()
    return jsonify({"success": True, "id": new_w.id})


@admin_bp.route("/dashboard/builder/delete-widget/<int:widget_id>", methods=["POST"])
@login_required
def dashboard_delete_widget(widget_id):
    if not ArasSystemSetting.get("dashboard_builder_enabled", False):
        return jsonify({"success": False, "error": "Builder disabled"}), 403
    
    w = AppManagerDashboard.query.get_or_404(widget_id)
    if w.user_id != current_user.id and not current_user.is_admin:
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    
    db.session.delete(w)
    db.session.commit()
    return jsonify({"success": True})


@admin_bp.route("/dashboard/builder/save-layout", methods=["POST"])
@login_required
def dashboard_save_layout():
    if not ArasSystemSetting.get("dashboard_builder_enabled", False):
        return jsonify({"success": False, "error": "Builder disabled"}), 403
    
    data = request.json or {} # Expect list of {id: db_id, order: X}
    for item in data.get("layout", []):
        wid = item.get("db_id")
        if not wid: continue
        w = AppManagerDashboard.query.get(wid)
        if w and (w.user_id == current_user.id or current_user.is_admin):
            w.order = item.get("order", 0)
    
    db.session.commit()
    return jsonify({"success": True})


@admin_bp.route("/notifications/<category>")
@login_required
def notifications(category):
    from arasCore.admin.models import Notification
    since  = request.args.get("since", 0.0, type=float)
    notifs = (
        current_user.notifications
        .filter(Notification.timestamp > since, Notification.category == category)
        .order_by(Notification.timestamp.asc())
    )
    return jsonify([
        {"name": n.name, "data": n.get_data(), "timestamp": n.timestamp, "category": n.category}
        for n in notifs
    ])


@admin_bp.route("/user-log/bulk-delete/", methods=["POST"])
@login_required
def userlog_bulk_delete():
    ids_raw = request.form.get("ids", "")
    ids = [int(i) for i in ids_raw.split(",") if i.strip().isdigit()]
    if ids:
        UserActivity.query.filter(
            UserActivity.id.in_(ids),
            UserActivity.user_id == current_user.id,
        ).delete(synchronize_session=False)
        db.session.commit()
    from flask import flash, redirect, url_for
    flash(f"Deleted {len(ids)} log entries.", "success")
    return redirect(url_for("admin.settings") + "#panel-userlog")


@admin_bp.route("/user-log", methods=["GET", "POST"])
@login_required
def user_log():
    from flask import request as _req
    current_user.last_activity_read_time = datetime.utcnow()
    current_user.add_notification("unread_activity_count", 0, category="activity")
    db.session.commit()

    q = _req.args.get("q", "").strip()
    query = current_user.activities.order_by(UserActivity.created_at.desc())
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(UserActivity.name.ilike(like), UserActivity.module.ilike(like))
        )
    activities = query.all()
    cols = [("Action", "name"), ("Module", "module"), ("Date", "created_at")]
    return render_template(
        "admin/gen/gen_view_list.html",
        title="User Log",
        main_title="User Log",
        items=activities,
        view_columns=cols,
        search_enabled=True,
        search_q=q,
        filter_cols=cols,
        active_filters=[],
    )
