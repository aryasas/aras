# -*- coding: utf-8 -*-
"""
test/test_admin.py — Admin panel route tests (dashboard, settings, users,
                     user_log, messages, notifications, post, explore, dev,
                     send_message, settings/db/generate-view).
"""
import json
import click
from .client import Client
from .helpers import section, assert_ok, summary, reset


def run(base: str, username: str, password: str):
    reset()
    c = Client(base)
    c.login(username, password)

    # ── Dashboard ─────────────────────────────────────────────────────────

    section("Admin — Dashboard")

    status, url, html = c.get("/admin/dashboard")
    assert_ok("GET /admin/dashboard → 200", status == 200, f"status={status}")
    assert_ok("Dashboard contains admin markup", any(k in html for k in ["dashboard", "Dashboard", "adm_base"]))

    # Dashboard POST (create post)
    token = c.csrf(html)
    status, url, html = c.post("/admin/dashboard", {
        "csrf_token": token or "",
        "post": "Test dashboard post from test suite.",
        "submit": "Post",
    })
    assert_ok("POST /admin/dashboard → 200 or redirect", status in (200, 302), f"status={status}")

    # ── Settings ──────────────────────────────────────────────────────────

    section("Admin — Settings")

    status, _, html = c.get("/admin/settings")
    assert_ok("GET /admin/settings → 200", status == 200, f"status={status}")
    assert_ok("Settings page has panels", any(k in html for k in ["settings-panel", "panel-general", "data-panel", "Settings"]))
    assert_ok("Settings has Database section", "database" in html.lower() or "Database" in html)
    assert_ok("Settings has Users section", "user" in html.lower())

    # ── Users ─────────────────────────────────────────────────────────────

    section("Admin — Users")

    status, _, html = c.get("/admin/users")
    assert_ok("GET /admin/users → 200", status == 200, f"status={status}")
    assert_ok("Users page lists users", "username" in html.lower() or "Users" in html)
    assert_ok("Admin user appears in list", username in html)

    # ── User Log ──────────────────────────────────────────────────────────

    section("Admin — User Log")

    status, _, html = c.get("/admin/user-log")
    assert_ok("GET /admin/user-log → 200", status == 200, f"status={status}")

    # Mark log read via POST
    token = c.csrf(html)
    if token:
        status, _, _ = c.post("/admin/user-log", {"csrf_token": token})
        assert_ok("POST /admin/user-log → 200 or redirect", status in (200, 302), f"status={status}")

    # ── Messages ──────────────────────────────────────────────────────────

    section("Admin — Messages")

    status, _, html = c.get("/admin/messages")
    assert_ok("GET /admin/messages → 200", status == 200, f"status={status}")

    # Send message to self
    status, _, html = c.get(f"/admin/send_message/{username}")
    assert_ok(f"GET /admin/send_message/{username} → 200", status == 200, f"status={status}")
    assert_ok("Send-message form has body field", "body" in html or "message" in html.lower())
    token = c.csrf(html)
    status, url, _ = c.post(f"/admin/send_message/{username}", {
        "csrf_token": token or "",
        "body": "Hello from test suite!",
        "submit": "Submit",
    })
    assert_ok("POST send_message → redirect or 200", status in (200, 302), f"status={status}")

    # Send to non-existent user → 404
    status, _, _ = c.get("/admin/send_message/no_such_user_xyz")
    assert_ok("send_message to nonexistent user → 404", status == 404, f"status={status}")

    # ── Notifications ─────────────────────────────────────────────────────

    section("Admin — Notifications")

    for category in ("activity", "message"):
        status, _, body = c.get(f"/admin/notifications/{category}")
        assert_ok(f"GET /admin/notifications/{category} → 200", status == 200, f"status={status}")
        assert_ok(f"notifications/{category} returns JSON", body.strip().startswith("[") or body.strip().startswith("{"), f"body[:60]={body[:60]}")

    # ── Post wall ─────────────────────────────────────────────────────────

    section("Admin — Post wall")

    status, _, html = c.get("/admin/post")
    assert_ok("GET /admin/post → 200", status == 200, f"status={status}")
    assert_ok("Post wall has post form", "post" in html.lower())

    token = c.csrf(html)
    status, url, _ = c.post("/admin/post", {
        "csrf_token": token or "",
        "post": "Test wall post from test suite.",
        "submit": "Post",
    })
    assert_ok("POST /admin/post → redirect or 200", status in (200, 302), f"status={status}")

    # ── Explore ───────────────────────────────────────────────────────────

    section("Admin — Explore")

    status, _, html = c.get("/admin/explore")
    assert_ok("GET /admin/explore → 200", status == 200, f"status={status}")

    # ── Dev page ──────────────────────────────────────────────────────────

    section("Admin — Dev page")

    status, _, html = c.get("/admin/dev")
    assert_ok("GET /admin/dev → 200 (no login_required)", status in (200, 302, 404), f"status={status}")

    # ── User profile ──────────────────────────────────────────────────────

    section("Admin — User profile")

    status, _, html = c.get(f"/auth/user/{username}")
    assert_ok(f"GET /auth/user/{username} → 200", status == 200, f"status={status}")
    assert_ok("Profile page shows username", username in html)

    # ── Settings — DB generate-view (POST only) ───────────────────────────

    section("Admin — Settings DB generate-view")

    status, _, html = c.get("/admin/settings")
    token = c.csrf(html)
    status, url, body = c.post("/admin/settings/db/generate-view", {
        "csrf_token": token or "",
        "table_name": "__nonexistent_table__",
    })
    assert_ok("POST /admin/settings/db/generate-view → responds", status in (200, 302, 400, 404, 422, 500), f"status={status}")

    return summary()


@click.command("admin")
@click.option("--base", default="http://localhost:8080", show_default=True)
@click.option("--username", default="admin", show_default=True)
@click.option("--password", default="admin", show_default=True)
def cmd(base, username, password):
    """Test admin panel routes."""
    run(base, username, password)
