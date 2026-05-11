# -*- coding: utf-8 -*-
"""
test/test_routes.py — Smoke test all known routes for correct status codes.
Covers: auth routes, admin routes, unauthenticated redirects, 404.
"""
import click
from .client import Client
from .helpers import section, assert_ok, summary, reset

# Public auth routes (no login needed)
AUTH_PUBLIC_ROUTES = [
    ("/auth/login",           200),
    ("/auth/register",        200),
    ("/auth/password-reset",  200),
]

# Auth routes that require login
AUTH_PROTECTED_ROUTES = [
    ("/auth/change-password", 200),
    ("/auth/change-email",    200),
]

# Admin routes (require login)
ADMIN_ROUTES = [
    ("/admin/dashboard",    200),
    ("/admin/settings",     200),
    ("/admin/users",        200),
    ("/admin/user-log",     200),
    ("/admin/messages",     200),
    ("/admin/apps",         200),
    ("/admin/apps/new",     200),
    ("/admin/post",         200),
    ("/admin/explore",      200),
    ("/admin/dev",          200),
]

# Notification categories
NOTIFICATION_CATEGORIES = ["activity", "message"]

# Routes that must redirect to login when unauthenticated
REDIRECT_WHEN_UNAUTH = [
    "/admin/dashboard",
    "/admin/settings",
    "/admin/users",
    "/admin/apps",
    "/admin/post",
    "/admin/explore",
    "/admin/user-log",
    "/admin/messages",
    "/auth/change-password",
    "/auth/change-email",
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

    # ── Public auth pages ─────────────────────────────────────────────────

    section("Routes — Auth public pages (unauthenticated)")

    for path, expected in AUTH_PUBLIC_ROUTES:
        status, _, _ = c.get(path)
        assert_ok(f"GET {path} → {expected}", status == expected, f"status={status}")

    # ── Authenticated routes ──────────────────────────────────────────────

    section("Routes — Admin & protected pages (authenticated)")

    c.login(username, password)

    for path, expected in ADMIN_ROUTES:
        status, _, _ = c.get(path)
        assert_ok(f"GET {path} → {expected}", status == expected, f"status={status}")

    for path, expected in AUTH_PROTECTED_ROUTES:
        status, _, _ = c.get(path)
        assert_ok(f"GET {path} → {expected}", status == expected, f"status={status}")

    # Notifications JSON endpoints
    for cat in NOTIFICATION_CATEGORIES:
        status, _, body = c.get(f"/admin/notifications/{cat}")
        assert_ok(f"GET /admin/notifications/{cat} → 200", status == 200, f"status={status}")
        assert_ok(f"notifications/{cat} → JSON", body.strip().startswith("[") or body.strip().startswith("{"), f"body[:40]={body[:40]}")

    # User profile
    status, _, _ = c.get(f"/auth/user/{username}")
    assert_ok(f"GET /auth/user/{username} → 200", status == 200, f"status={status}")

    # Login page redirects when already authenticated
    status, url, _ = c.get("/auth/login")
    assert_ok("GET /auth/login (logged in) → redirect away", "dashboard" in url or status in (200, 302), f"url={url}")

    # ── 404 handling ──────────────────────────────────────────────────────

    section("Routes — 404 for unknown paths")

    status, _, _ = c.get("/this-path-does-not-exist-xyz-404")
    assert_ok("Unknown path → 404", status == 404, f"status={status}")

    status, _, _ = c.get("/admin/apps/999999/edit")
    assert_ok("GET /admin/apps/999999/edit → 404", status == 404, f"status={status}")

    return summary()


@click.command("routes")
@click.option("--base",     default="http://localhost:8080", show_default=True)
@click.option("--username", default="admin",  show_default=True)
@click.option("--password", default="admin",  show_default=True)
def cmd(base, username, password):
    """Smoke test all known routes."""
    run(base, username, password)
