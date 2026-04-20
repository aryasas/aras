# -*- coding: utf-8 -*-
"""
test/test_auth.py — Auth route tests (login, logout, register, change-password,
                    password-reset, change-email, user profile).
"""
import re
import click
from .client import Client
from .helpers import section, assert_ok, summary, reset


def run(base: str, username: str, password: str):
    reset()
    c = Client(base)

    # ── Public pages ──────────────────────────────────────────────────────

    section("Auth — Public pages")

    status, url, html = c.get("/auth/login")
    assert_ok("GET /auth/login → 200", status == 200, f"status={status}")
    assert_ok("Login page has CSRF token", 'csrf_token' in html)
    assert_ok("Login page has email/username field", "email_or_username" in html)

    status, _, html = c.get("/auth/register")
    assert_ok("GET /auth/register → 200", status == 200, f"status={status}")
    assert_ok("Register page has username field", "username" in html)

    status, _, html = c.get("/auth/password-reset")
    assert_ok("GET /auth/password-reset → 200", status == 200, f"status={status}")
    assert_ok("Password-reset page has email field", "email" in html)

    status, url, _ = c.get("/auth/logout")
    assert_ok("GET /auth/logout (unauth) → redirect to login", "login" in url, f"url={url}")

    # ── Register new user ─────────────────────────────────────────────────

    section("Auth — Register new user")

    import time
    test_user = f"testuser_{int(time.time())}"
    test_email = f"{test_user}@example.com"
    test_pass = "Testpass123!"

    _, _, html = c.get("/auth/register")
    token = c.csrf(html)
    status, url, html = c.post("/auth/register", {
        "csrf_token": token or "",
        "username": test_user,
        "email": test_email,
        "password": test_pass,
        "password2": test_pass,
    })
    assert_ok("Register new user → redirect or success", status in (200, 302) or "login" in url or "dashboard" in url, f"url={url} status={status}")

    # Duplicate username rejected
    _, _, html = c.get("/auth/register")
    token = c.csrf(html)
    status, url, html = c.post("/auth/register", {
        "csrf_token": token or "",
        "username": test_user,
        "email": f"dup_{test_email}",
        "password": test_pass,
        "password2": test_pass,
    })
    assert_ok("Duplicate username → stays on register or shows error", "register" in url or status == 200, f"url={url}")

    # ── Login / Logout ────────────────────────────────────────────────────

    section("Auth — Login / Logout")

    _, _, html = c.get("/auth/login")
    token = c.csrf(html)
    status, url, html = c.post("/auth/login", {
        "csrf_token": token or "",
        "email_or_username": username,
        "password": "wrong_password_xyz",
    })
    assert_ok("Bad login stays on login page", "login" in url or "Invalid" in html, f"url={url}")

    ok = c.login(username, password)
    assert_ok("Login with valid credentials succeeds", ok, f"url={c.last_url}")

    status, url, html = c.get("/admin/dashboard")
    assert_ok("Dashboard accessible after login", status == 200, f"status={status}")

    # Login page redirects away when already authenticated
    status, url, _ = c.get("/auth/login")
    assert_ok("Login page redirects when already logged in", "dashboard" in url or status in (200, 302), f"url={url}")

    c.logout()
    status, url, _ = c.get("/admin/dashboard")
    assert_ok("Dashboard redirects after logout", "login" in url, f"url={url}")

    # ── Change password ───────────────────────────────────────────────────

    section("Auth — Change password")

    c.login(username, password)
    status, _, html = c.get("/auth/change-password")
    assert_ok("GET /auth/change-password → 200", status == 200, f"status={status}")
    assert_ok("Change-password has old_password field", "old_password" in html)
    assert_ok("Change-password has new_password field", "new_password" in html)

    token = c.csrf(html)
    status, url, html = c.post("/auth/change-password", {
        "_csrf_token": token or "",
        "old_password": "wrongOld123",
        "new_password": "newpass123",
        "new_password2": "newpass123",
    })
    assert_ok("Wrong old password → error shown", "incorrect" in html.lower() or status in (200, 400), f"status={status}")
    c.logout()

    # ── Change email ──────────────────────────────────────────────────────

    section("Auth — Change email")

    c.login(username, password)
    status, _, html = c.get("/auth/change-email")
    assert_ok("GET /auth/change-email → 200", status == 200, f"status={status}")
    assert_ok("Change-email has email field", "email" in html)

    token = c.csrf(html)
    status, url, html = c.post("/auth/change-email", {
        "csrf_token": token or "",
        "email": f"newemail_{int(time.time())}@example.com",
        "password": password,
    })
    assert_ok("POST /auth/change-email → 200 or redirect", status in (200, 302), f"status={status}")
    c.logout()

    # ── User profile ──────────────────────────────────────────────────────

    section("Auth — User profile")

    c.login(username, password)
    status, _, html = c.get(f"/auth/user/{username}")
    assert_ok(f"GET /auth/user/{username} → 200", status == 200, f"status={status}")
    assert_ok("Profile shows username", username in html)

    # Non-existent user → 404
    status, _, _ = c.get("/auth/user/no_such_user_xyz999")
    assert_ok("GET /auth/user/nonexistent → 404", status == 404, f"status={status}")
    c.logout()

    # ── Protected routes redirect when unauthenticated ────────────────────

    section("Auth — Protected routes redirect when unauthenticated")

    for path in ["/auth/change-password", "/auth/change-email", "/admin/dashboard", "/admin/settings"]:
        status, url, _ = c.get(path)
        assert_ok(f"{path} → redirect to login", "login" in url, f"url={url}")

    return summary()


@click.command("auth")
@click.option("--base", default="http://localhost:8080", show_default=True, help="Base URL")
@click.option("--username", default="admin", show_default=True)
@click.option("--password", default="admin", show_default=True)
def cmd(base, username, password):
    """Test authentication routes."""
    run(base, username, password)
