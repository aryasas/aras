# -*- coding: utf-8 -*-
from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from arasCore.arasAdmin import arasAdmin_bp
from arasCore.arasAdmin.models import UserActivity
from arasCore.arasAdmin.services import get_dashboard_widgets
from arasCore.lib.extensions import db


@arasAdmin_bp.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    widgets = get_dashboard_widgets(current_user)
    return render_template(
        "admin/dashboard.html",
        title="Dashboard",
        main_title="Admin Dashboard",
        user=current_user,
        widgets=widgets,
    )


@arasAdmin_bp.route("/notifications/<category>")
@login_required
def notifications(category):
    from arasCore.arasAdmin.models import Notification
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


@arasAdmin_bp.route("/user-log/bulk-delete/", methods=["POST"])
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


@arasAdmin_bp.route("/user-log", methods=["GET", "POST"])
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
        "admin/aras_list.html",
        title="User Log",
        main_title="User Log",
        items=activities,
        view_columns=cols,
        search_enabled=True,
        search_q=q,
        filter_cols=cols,
        active_filters=[],
    )
