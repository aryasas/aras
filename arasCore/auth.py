# -*- coding: utf-8 -*-
"""
arasCore/auth.py
Auth layer — User model, login/logout services, token, decorators.
Merged from app_auth/models.py, helpers.py, token.py, decorators.py
"""
from functools import wraps
from flask import redirect, url_for, flash, abort, current_app
from flask_login import current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from .lib.extensions import db, login_manager
import json


# ── User Model ────────────────────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = "auth_users"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email         = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active     = db.Column(db.Boolean, default=True)
    is_admin      = db.Column(db.Boolean, default=False)
    created_at    = db.Column(db.DateTime, default=db.func.now())
    updated_at    = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    # Messaging timestamps
    # last_message_read_time  = db.Column(db.DateTime)
    last_activity_read_time = db.Column(db.DateTime)

    roles = db.relationship("UserRole", back_populates="user", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_slug):
        return any(ur.role.slug == role_slug for ur in self.roles)

    def has_permission(self, app_slug, resource_slug=None, action="view", module_slug=None):
        from arasCore.rbac import check_permission
        return check_permission(self, app_slug, resource_slug, action, module_slug)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def get_reset_token(self, expires=3600):
        from itsdangerous import URLSafeTimedSerializer
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        return s.dumps(self.id, salt="password-reset")

    @staticmethod
    def verify_reset_token(token, expires=3600):
        from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        try:
            user_id = s.loads(token, salt="password-reset", max_age=expires)
        except (SignatureExpired, BadSignature):
            return None
        return User.query.get(user_id)

    def get_email_change_token(self, new_email, expires=3600):
        from itsdangerous import URLSafeTimedSerializer
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        return s.dumps({"id": self.id, "email": new_email}, salt="email-change")

    @staticmethod
    def verify_email_change_token(token, expires=3600):
        from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token, salt="email-change", max_age=expires)
        except (SignatureExpired, BadSignature):
            return None, None
        return User.query.get(data["id"]), data["email"]

    def gravatar(self, size=32):
        import hashlib
        digest = hashlib.md5(self.email.lower().encode()).hexdigest()
        return f"https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}"

    # def new_messages(self):
    #     from arasCore.arasAdmin.models import Message
    #     from datetime import datetime
    #     last_read = self.last_message_read_time or datetime(1900, 1, 1)
    #     return (
    #         Message.query
    #         .filter_by(recipient_id=self.id)
    #         .filter(Message.timestamp > last_read)
    #         .count()
    #     )

    def new_activities(self):
        from arasCore.arasAdmin.models import UserActivity
        from datetime import datetime
        last_read = self.last_activity_read_time or datetime(1900, 1, 1)
        return (
            UserActivity.query
            .filter_by(user_id=self.id)
            .filter(UserActivity.created_at > last_read)
            .count()
        )

    def log_activity(self, name, module=None, payload=None):
        from arasCore.arasAdmin.models import UserActivity
        import json as _json
        entry = UserActivity(
            user_id=self.id,
            name=name,
            module=module,
            payload_json=_json.dumps(payload) if payload else None,
        )
        db.session.add(entry)
        self.add_notification(
            "unread_activity_count",
            (self.new_activities() + 1),
            category="activity",
        )

    def add_notification(self, name, data, category="general"):
        from arasCore.arasAdmin.models import Notification
        # Remove existing same-name notification for this user
        self.notifications.filter_by(name=name).delete()
        n = Notification(
            name=name,
            user_id=self.id,
            payload_json=json.dumps(data),
            category=category,
        )
        db.session.add(n)
        return n

    def __repr__(self):
        return f"<User {self.username}>"


# ── Flask-Login loader ────────────────────────────────────────────────────────

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ── Auth Services ─────────────────────────────────────────────────────────────

def authenticate(username_or_email, password):
    """Return User if credentials valid, else None."""
    user = (
        User.query.filter_by(username=username_or_email).first()
        or User.query.filter_by(email=username_or_email).first()
    )
    if user and user.check_password(password):
        return user
    return None


def login(user, remember=False):
    login_user(user, remember=remember)


def logout():
    logout_user()


def create_user(username, email, password, is_admin=False):
    user = User(username=username, email=email, is_admin=is_admin)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


# ── Decorators ────────────────────────────────────────────────────────────────

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def require_role(role_slug):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if not current_user.has_role(role_slug):
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator


def require_permission(app_slug, resource_slug=None, action="view", module_slug=None):
    """Thin wrapper — delegates to rbac.require_permission for import compat."""
    from arasCore.rbac import require_permission as _rbac_require
    return _rbac_require(app_slug, resource_slug, action, module_slug)


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ── Late binding — ensure UserRole backref is set ────────────────────────────
# This runs after permissions.py is imported by __init__.py
def _setup_user_roles_relationship():
    from .permissions import UserRole  # noqa: F401
    if not hasattr(User, 'roles') or User.roles is None:
        User.roles = db.relationship("UserRole", back_populates="user", lazy="dynamic")
