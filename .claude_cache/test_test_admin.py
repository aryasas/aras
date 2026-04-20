# -*- coding: utf-8 -*-
"""
test/test_admin.py — Admin panel route tests (dashboard, settings, users, activities).
"""
import click
from .client import Client
from .helpers import section, assert_ok, summary, reset


def run(base: str, username: str, password: str):
    reset()
    c = Client(base)
    c.login(username, password)

    section("Admin — Dashboard")

    status, url, html = c.get("/admin/dashboard")
    assert_ok("GET /admin/dashboard → 200", status == 200, f"status={status}")
    assert_ok("Dashboard contains admin markup", any(k in html for k in ["dashboard", "Dashboard", "adm_base"]))

    section("Admin — Settings")

    status, _, html = c.get("/admin/settings")
    assert_ok("GET /admin/settings → 200", status == 200, f"status={status}")
    assert_ok("Settings page has panels", "settings-panel" in html or "settings-nav" in html or "Settings" in html)
    assert_ok("Settings has Database panel", "database" in html.lower() or "Database" in html)

    section("Admin — Users")

    status, _, html = c.get("/admin/users")
    assert_ok("GET /admin/users → 200", status == 200, f"status={status}")
    assert_ok("Users page lists users", "username" in html.lower() or "Users" in html)

    section("Admin — Activities")

    status, _, html = c.get("/admin/activities")
    assert_ok("GET /admin/activities → 200", status == 200, f"status={status}")

    section("Admin — Messages")

    status, _, html = c.get("/admin/messages")
    assert_ok("GET /admin/messages → 200", status == 200, f"status={status}")

    section("Admin — Notifications JSON")

    status, _, body = c.get("/admin/notifications/activity")
    assert_ok("GET /admin/notifications/activity → 200", status == 200, f"status={status}")
    assert_ok("Notifications returns JSON list", body.strip().startswith("[") or body.strip().startswith("{"), f"body[:50]={body[:50]}")

    section("Admin — User profile")

    status, _, html = c.get(f"/auth/user/{username}")
    assert_ok(f"GET /auth/user/{username} → 200", status == 200, f"status={status}")
    assert_ok("Profile page shows username", username in html)

    return summary()


@click.command("admin")
@click.option("--base", default="http://localhost:8080", show_default=True)
@click.option("--username", default="admin", show_default=True)
@click.option("--password", default="admin", show_default=True)
def cmd(base, username, password):
    """Test admin panel routes."""
    run(base, username, password)
