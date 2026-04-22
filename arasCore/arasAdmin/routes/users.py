# -*- coding: utf-8 -*-
import csv, io

from flask import render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user

from arasCore.arasAdmin import arasAdmin_bp
from arasCore.lib.extensions import db
from arasCore.auth import User
from arasCore.arasAdmin.forms import CreateUserForm


@arasAdmin_bp.route("/users")
@login_required
def users():
    q = request.args.get("q", "").strip()
    query = User.query.order_by(User.created_at.desc())
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(User.username.ilike(like), User.email.ilike(like))
        )
    all_users = query.all()
    cols = [("Username", "username"), ("Email", "email"), ("Admin", "is_admin"), ("Active", "is_active"), ("Joined", "created_at")]
    return render_template(
        "admin/aras_list.html",
        title="Users",
        main_title="Users",
        items=all_users,
        view_columns=cols,
        add_url=url_for("admin.users_new"),
        search_enabled=True,
        search_q=q,
        filter_cols=cols,
        active_filters=[],
        extra_buttons=[
            {"label": "Export CSV", "url": url_for("admin.users_export_csv"), "icon": "fa-download", "style": "outline"},
        ],
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


@arasAdmin_bp.route("/users/<int:user_id>/", methods=["GET"])
@login_required
def user_detail(user_id):
    u = User.query.get_or_404(user_id)
    from arasCore.arasAdmin.models import UserActivity
    recent_activities = u.activities.order_by(UserActivity.created_at.desc()).limit(20).all()
    return render_template(
        "admin/user_profile.html",
        title=u.username,
        main_title=u.username,
        user=u,
        recent_activities=recent_activities,
    )


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
    u      = User.query.get_or_404(user_id)
    u.is_admin = not u.is_admin
    status = "granted" if u.is_admin else "revoked"
    current_user.log_activity(f"admin_{status}", module="users", payload={"target": u.username})
    db.session.commit()
    flash(f"Admin {status} for '{u.username}'.", "success")
    return redirect(url_for("admin.users"))


@arasAdmin_bp.route("/users/export-csv")
@login_required
def users_export_csv():
    all_users = User.query.order_by(User.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "username", "email", "is_admin", "is_active", "created_at"])
    for u in all_users:
        writer.writerow([u.id, u.username, u.email, u.is_admin, u.is_active,
                         u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else ""])
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=users.csv"},
    )


@arasAdmin_bp.route("/users/bulk-delete/", methods=["POST"])
@login_required
def users_bulk_delete():
    ids_raw = request.form.get("ids", "")
    ids = [int(i) for i in ids_raw.split(",") if i.strip().isdigit()]
    deleted = 0
    for uid in ids:
        if uid == current_user.id:
            continue
        u = User.query.get(uid)
        if u:
            db.session.delete(u)
            deleted += 1
    db.session.commit()
    flash(f"Deleted {deleted} user(s).", "danger")
    return redirect(url_for("admin.settings") + "#panel-users")
