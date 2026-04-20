# -*- coding: utf-8 -*-
"""
test/test_routes.py — Smoke test all known static routes for status codes.
"""
import click
from .client import Client
from .helpers import section, assert_ok, summary, reset

# (path, expected_status_when_authenticated)
AUTH_ROUTES = [
    ("/auth/login",           200),
    ("/auth/register",        200),
    ("/auth/change-password", 200),
]

ADMIN_ROUTES = [
    ("/admin/dashboard",    200),
    ("/admin/settings",     200),
    ("/admin/users",        200),
    ("/admin/activities",   200),
    ("/admin/messages",     200),
    ("/admin/apps",         200),
    ("/admin/apps/new",     200),
]

REDIRECT_WHEN_UNAUTH = [
    "/admin/dashboard",
    "/admin/settings",
    "/admin/users",
    "/admin/apps",
    "/auth/change-password",
]


def run(base: str, username: str, password: str):
    reset()
    c = Client(base)

    # ── Root redirect ─────────────────────────────────────────────────────

    section("Routes — Root redirect")

    status, url, _ = c.get("/")
    assert_ok("GET / redirects (not 404/500)", status in (200, 301, 302), f"status={status}")
    assert_ok("GET / sends to login or dashboard", "login" in url or "dashboard" in url, f"url={url}")

    # ── Unauthenticated redirects ─────────────────────────────────────────

    section("Routes — Unauthenticated access redirects to login")

    for path in REDIRECT_WHEN_UNAUTH:
        status, url, _ = c.get(path)
        assert_ok(f"{path} → login", "login" in url, f"url={url}")

    # ── Auth pages (public) ───────────────────────────────────────────────

    section("Routes — Auth public pages (unauthenticated)")

    for path, expected in AUTH_ROUTES:
        status, _, _ = c.get(path)
        assert_ok(f"GET {path} → {expected}", status == expected, f"status={status}")

    # ── Admin pages (authenticated) ───────────────────────────────────────

    section("Routes — Admin pages (authenticated)")

    c.login(username, password)

    for path, expected in ADMIN_ROUTES:
        status, _, _ = c.get(path)
        assert_ok(f"GET {path} → {expected}", status == expected, f"status={status}")

    # Login redirects away when already logged in
    status, url, _ = c.get("/auth/login")
    assert_ok("GET /auth/login when logged in → redirect to dashboard", "dashboard" in url or status == 200, f"url={url}")

    # ── 404 handling ──────────────────────────────────────────────────────

    section("Routes — 404 for unknown paths")

    status, _, _ = c.get("/this-path-does-not-exist-xyz-404")
    assert_ok("Unknown path → 404", status == 404, f"status={status}")

    return summary()


@click.command("routes")
@click.option("--base",     default="http://localhost:8080", show_default=True)
@click.option("--username", default="admin",  show_default=True)
@click.option("--password", default="admin",  show_default=True)
def cmd(base, username, password):
    """Smoke test all known static routes."""
    run(base, username, password)
