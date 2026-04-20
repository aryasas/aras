# -*- coding: utf-8 -*-
"""arasCore/routes.py — Auth blueprint: /login /logout /register /password-reset"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from .auth import authenticate, login, logout, create_user
from .forms import LoginForm, RegisterForm, ChangePasswordForm

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")



@auth_bp.route("/login", methods=["GET", "POST"])
def login_view():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = authenticate(form.email_or_username.data, form.password.data)
        if user:
            login(user, remember=form.remember_me.data)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("admin.dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
def logout_view():
    logout()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login_view"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register_view():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        from .auth import User
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered.", "warning")
        elif User.query.filter_by(username=form.username.data).first():
            flash("Username taken.", "warning")
        else:
            create_user(form.username.data, form.email.data, form.password.data)
            flash("Account created. Please log in.", "success")
            return redirect(url_for("auth.login_view"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/password-reset", methods=["GET", "POST"])
def password_reset_request():
    """Placeholder — full implementation later."""
    flash("Password reset is not yet available.", "info")
    return redirect(url_for("auth.login_view"))


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.old_password.data):
            flash("Current password is incorrect.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            from .lib.extensions import db
            db.session.commit()
            flash("Password changed successfully.", "success")
            return redirect(url_for("admin.dashboard"))
    return render_template("auth/change_password.html", form=form)


@auth_bp.route("/user/<username>")
@login_required
def user(username):
    from .auth import User
    from .arasAdmin.models import UserActivity
    u = User.query.filter_by(username=username).first_or_404()
    recent_activities = (
        UserActivity.query
        .filter_by(user_id=u.id)
        .order_by(UserActivity.created_at.desc())
        .limit(10)
        .all()
    )
    return render_template("admin/user_profile.html",
                           title=u.username,
                           main_title="User Profile",
                           user=u,
                           recent_activities=recent_activities)


@auth_bp.route("/change-email", methods=["GET", "POST"])
@login_required
def change_email_request():
    """Placeholder — full implementation later."""
    flash("Change email is not yet available.", "info")
    return redirect(url_for("admin.dashboard"))


@auth_bp.route("/change-email/<token>")
@login_required
def change_email(token):
    """Placeholder — full implementation later."""
    flash("Email change confirmation not yet implemented.", "info")
    return redirect(url_for("admin.dashboard"))
