# -*- coding: utf-8 -*-
"""arasCore/routes.py — Auth blueprint: /login /logout /register /password-reset"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from .auth import authenticate, login, logout, create_user, User
from .forms import LoginForm, RegisterForm, ChangePasswordForm, PasswordResetRequestForm, PasswordResetForm, ChangeEmailForm

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
            from .lib.extensions import db
            user.log_activity("login", module="auth")
            db.session.commit()
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
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.get_reset_token()
            reset_url = url_for("auth.password_reset", token=token, _external=True)
            mail_enabled = current_app.config.get("MAIL_USERNAME")
            if mail_enabled:
                from .lib.email import send_email
                send_email(
                    subject="[Aras] Password Reset",
                    sender=current_app.config["MAIL_SENDER"],
                    recipients=[user.email],
                    text_body=f"Reset your password: {reset_url}",
                    html_body=f'<p>Reset your password: <a href="{reset_url}">{reset_url}</a></p>',
                )
                flash("Reset link sent to your email.", "info")
            else:
                flash(f"Reset link (copy this): {reset_url}", "info")
        else:
            flash("No account found with that email.", "warning")
        return redirect(url_for("auth.login_view"))
    return render_template("auth/password_reset_request.html", form=form)


@auth_bp.route("/password-reset/<token>", methods=["GET", "POST"])
def password_reset(token):
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))
    user = User.verify_reset_token(token)
    if not user:
        flash("Reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.password_reset_request"))
    form = PasswordResetForm()
    if form.validate_on_submit():
        from .lib.extensions import db
        user.set_password(form.password.data)
        user.log_activity("password_reset", module="auth")
        db.session.commit()
        flash("Password reset. Please log in.", "success")
        return redirect(url_for("auth.login_view"))
    return render_template("auth/password_reset.html", form=form, token=token)


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
            current_user.log_activity("password_changed", module="auth")
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
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.password.data):
            flash("Current password is incorrect.", "danger")
        elif User.query.filter_by(email=form.email.data).first():
            flash("That email is already in use.", "warning")
        else:
            token = current_user.get_email_change_token(form.email.data)
            confirm_url = url_for("auth.change_email", token=token, _external=True)
            mail_enabled = current_app.config.get("MAIL_USERNAME")
            if mail_enabled:
                from .lib.email import send_email
                send_email(
                    subject="[Aras] Confirm Email Change",
                    sender=current_app.config["MAIL_SENDER"],
                    recipients=[form.email.data],
                    text_body=f"Confirm your new email: {confirm_url}",
                    html_body=f'<p>Confirm your new email: <a href="{confirm_url}">{confirm_url}</a></p>',
                )
                flash("Confirmation link sent to your new email.", "info")
            else:
                flash(f"Confirm link (copy this): {confirm_url}", "info")
            return redirect(url_for("admin.dashboard"))
    return render_template("auth/change_email.html", form=form)


@auth_bp.route("/change-email/<token>")
@login_required
def change_email(token):
    user, new_email = User.verify_email_change_token(token)
    if not user or user.id != current_user.id:
        flash("Confirmation link is invalid or has expired.", "danger")
        return redirect(url_for("admin.dashboard"))
    from .lib.extensions import db
    current_user.email = new_email
    current_user.log_activity("email_changed", module="auth", payload={"new_email": new_email})
    db.session.commit()
    flash("Email address updated.", "success")
    return redirect(url_for("admin.dashboard"))
