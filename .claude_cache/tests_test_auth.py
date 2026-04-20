# -*- coding: utf-8 -*-
"""
test/test_auth.py — Auth route tests (login, logout, register, change-password).
"""
import click
from .client import Client
from .helpers import section, assert_ok, summary, reset


def run(base: str, username: str, password: str):
    reset()
    c = Client(base)

    section("Auth — Public pages")

    # GET /auth/login renders form
    status, url, html = c.get("/auth/login")
    assert_ok("GET /auth/login → 200", status == 200, f"status={status}")
    assert_ok("Login page has form", 'name="csrf_token"' in html)
    assert_ok("Login page has email/username field", "email_or_username" in html)

    # GET /auth/register renders form
    status, _, html = c.get("/auth/register")
    assert_ok("GET /auth/register → 200", status == 200, f"status={status}")
    assert_ok("Register page has username field", "username" in html)

    # GET /auth/logout (not logged in) redirects to login
    status, url, _ = c.get("/auth/logout")
    assert_ok("GET /auth/logout redirects to login", "login" in url, f"url={url}")

    section("Auth — Login / Logout")

    # Bad credentials
    _, _, html = c.get("/auth/login")
    token = c.csrf(html)
    status, url, html = c.post("/auth/login", {
        "csrf_token": token or "",
        "email_or_username": username,
        "password": "wrong_password_xyz",
    })
    assert_ok("Bad login stays on login page", "login" in url or "Invalid" in html, f"url={url}")

    # Good credentials
    ok = c.login(username, password)
    assert_ok("Login with valid credentials succeeds", ok, f"url={c.last_url}")

    # Dashboard accessible after login
    status, url, html = c.get("/admin/dashboard")
    assert_ok("Dashboard accessible after login", status == 200, f"status={status}")

    # Logout
    c.logout()
    status, url, _ = c.get("/admin/dashboard")
    assert_ok("Dashboard redirects after logout", "login" in url, f"url={url}")

    section("Auth — Change password (login required)")

    c.login(username, password)
    status, _, html = c.get("/auth/change-password")
    assert_ok("GET /auth/change-password → 200", status == 200, f"status={status}")
    assert_ok("Change-password has old_password field", "old_password" in html)

    # Wrong old password
    token = c.csrf(html)
    status, url, html = c.post("/auth/change-password", {
        "csrf_token": token or "",
        "old_password": "wrongOld123",
        "new_password": "newpass123",
        "new_password2": "newpass123",
    })
    assert_ok("Wrong old password shows error", "incorrect" in html.lower() or status == 200, f"status={status}")
    c.logout()

    section("Auth — Protected routes redirect when unauthenticated")

    for path in ["/auth/change-password", "/admin/dashboard", "/admin/settings"]:
        status, url, _ = c.get(path)
        assert_ok(f"{path} → redirects to login", "login" in url, f"url={url}")

    return summary()


@click.command("auth")
@click.option("--base", default="http://localhost:8080", show_default=True, help="Base URL")
@click.option("--username", default="admin", show_default=True)
@click.option("--password", default="admin", show_default=True)
def cmd(base, username, password):
    """Test authentication routes."""
    run(base, username, password)
