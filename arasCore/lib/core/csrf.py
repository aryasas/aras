# -*- coding: utf-8 -*-
"""Simple CSRF protection without flask_wtf."""
import hmac, hashlib, secrets
from flask import session, request, abort, current_app


def _secret():
    return current_app.secret_key


def generate_csrf():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(32)
    tok = session["_csrf"]
    sig = hmac.new(_secret().encode() if isinstance(_secret(), str) else _secret(),
                   tok.encode(), hashlib.sha256).hexdigest()
    return f"{tok}.{sig}"


def validate_csrf(token):
    if not token:
        return False
    parts = token.split(".", 1)
    if len(parts) != 2:
        return False
    tok, sig = parts
    expected = hmac.new(_secret().encode() if isinstance(_secret(), str) else _secret(),
                        tok.encode(), hashlib.sha256).hexdigest()
    return session.get("_csrf") == tok and hmac.compare_digest(sig, expected)


def csrf_protect():
    """Call on POST/PUT/DELETE to abort 400 if token invalid."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    token = (request.form.get("csrf_token")
             or request.headers.get("X-CSRFToken")
             or request.headers.get("X-CSRF-Token"))
    if not validate_csrf(token):
        abort(400, "CSRF validation failed")


def register_csrf(app):
    app.jinja_env.globals["csrf_token"] = generate_csrf

    @app.before_request
    def _csrf_check():
        # Skip API and static
        if request.path.startswith("/api/") or request.path.startswith("/static/"):
            return
        csrf_protect()
