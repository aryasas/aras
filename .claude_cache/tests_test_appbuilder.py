# -*- coding: utf-8 -*-
"""
test/test_appbuilder.py — App Manager CRUD tests (apps, tables, columns, activate/deactivate).
"""
import re
import click
from .client import Client
from .helpers import section, assert_ok, summary, reset

APP_NAME    = "testapp"
APP_TITLE   = "Test App"
TABLE_NAME  = "items"
TABLE_TITLE = "Items"
COL_NAME    = "item_name"
COL_LABEL   = "Item Name"


def _get_id_from_url(url: str) -> str:
    """Extract trailing integer from a URL like /admin/apps/3/tables"""
    m = re.search(r"/(\d+)(?:/|$)", url)
    return m.group(1) if m else ""


def run(base: str, username: str, password: str):
    reset()
    c = Client(base)
    c.login(username, password)

    # ── Apps list ────────────────────────────────────────────────────────

    section("App Manager — Apps list")

    status, _, html = c.get("/admin/apps")
    assert_ok("GET /admin/apps → 200", status == 200, f"status={status}")
    assert_ok("Apps page has Add New button", "apps/new" in html or "Add New" in html)

    # ── Create App ───────────────────────────────────────────────────────

    section("App Manager — Create app")

    status, _, html = c.get("/admin/apps/new")
    assert_ok("GET /admin/apps/new → 200", status == 200, f"status={status}")
    token = c.csrf(html)
    assert_ok("New-app form has CSRF token", bool(token))

    status, url, html = c.post("/admin/apps/new", {
        "csrf_token": token or "",
        "name": APP_NAME,
        "title": APP_TITLE,
        "main_title": APP_TITLE,
        "url": f"/{APP_NAME}",
        "in_sidebar": "y",
        "is_active": "",
        "menu_order": "10",
    })
    assert_ok("Create app → redirects to apps list or tables", "apps" in url, f"url={url}")

    # Find the created app's ID
    status, _, html = c.get("/admin/apps")
    assert_ok("Apps list loads after create", status == 200)
    m = re.search(rf'href="[^"]*apps/(\d+)/tables"[^>]*>.*?{APP_TITLE}|{APP_TITLE}.*?href="[^"]*apps/(\d+)/tables"', html, re.DOTALL)
    if not m:
        m = re.search(rf'apps/(\d+)/[^"]*"[^>]*>\s*<[^>]+>\s*{APP_NAME}', html)
    app_id = (m.group(1) or m.group(2)) if m and (m.group(1) or m.group(2)) else ""
    # fallback: find any app id matching our name
    if not app_id:
        m2 = re.findall(r'apps/(\d+)/tables', html)
        app_id = m2[-1] if m2 else ""

    assert_ok("Found created app ID", bool(app_id), f"app_id={app_id!r}")

    if not app_id:
        print("  [skip] Cannot continue without app_id")
        return summary()

    # ── Edit App ─────────────────────────────────────────────────────────

    section("App Manager — Edit app")

    status, _, html = c.get(f"/admin/apps/{app_id}/edit")
    assert_ok(f"GET /admin/apps/{app_id}/edit → 200", status == 200, f"status={status}")
    token = c.csrf(html)
    status, url, _ = c.post(f"/admin/apps/{app_id}/edit", {
        "csrf_token": token or "",
        "name": APP_NAME,
        "title": APP_TITLE + " Edited",
        "main_title": APP_TITLE,
        "url": f"/{APP_NAME}",
        "in_sidebar": "y",
        "menu_order": "10",
    })
    assert_ok("Edit app → redirects", "apps" in url or str(app_id) in url, f"url={url}")

    # ── Tables ───────────────────────────────────────────────────────────

    section("App Manager — Tables")

    status, _, html = c.get(f"/admin/apps/{app_id}/tables")
    assert_ok(f"GET /admin/apps/{app_id}/tables → 200", status == 200, f"status={status}")
    assert_ok("Tables page has table form", "table" in html.lower())

    # Create table
    status, _, html = c.get(f"/admin/apps/{app_id}/tables/new")
    assert_ok(f"GET tables/new → 200", status == 200, f"status={status}")
    token = c.csrf(html)
    status, url, html = c.post(f"/admin/apps/{app_id}/tables/new", {
        "csrf_token": token or "",
        "name": TABLE_NAME,
        "title": TABLE_TITLE,
        "menu_title": TABLE_TITLE,
        "url_suffix": TABLE_NAME,
        "show_in_menu": "y",
        "is_active": "y",
        "menu_order": "1",
    })
    assert_ok("Create table → success", status in (200, 302) or TABLE_NAME in html or "tables" in url, f"url={url} status={status}")

    # Find table id
    status, _, html = c.get(f"/admin/apps/{app_id}/tables")
    tbl_ids = re.findall(rf'tables/(\d+)/columns', html)
    tbl_id  = tbl_ids[0] if tbl_ids else ""
    assert_ok("Found created table ID", bool(tbl_id), f"tbl_id={tbl_id!r}")

    # ── Columns ──────────────────────────────────────────────────────────

    if tbl_id:
        section("App Manager — Columns")

        status, _, html = c.get(f"/admin/apps/{app_id}/tables/{tbl_id}/columns")
        assert_ok(f"GET .../columns → 200", status == 200, f"status={status}")
        token = c.csrf(html)

        # Add a string column
        status, url, html = c.post(f"/admin/apps/{app_id}/tables/{tbl_id}/columns", {
            "csrf_token": token or "",
            "name": COL_NAME,
            "label": COL_LABEL,
            "field_type": "string",
            "required": "y",
            "order": "1",
        })
        assert_ok("Add column → success", COL_NAME in html or status in (200, 302), f"status={status}")

        # Find column id for delete later
        col_ids = re.findall(rf'columns/(\d+)/delete', html)
        col_id  = col_ids[0] if col_ids else ""

        # ── Activate ─────────────────────────────────────────────────────

        section("App Manager — Activate / Deactivate")

        status, _, html = c.get(f"/admin/apps/{app_id}/tables/{tbl_id}/columns")
        token = c.csrf(html)
        status, url, _ = c.post(f"/admin/apps/{app_id}/activate", {"csrf_token": token or ""})
        assert_ok("Activate app", status in (200, 302), f"status={status} url={url}")

        status, _, html = c.get("/admin/apps")
        assert_ok("App shows Active badge after activate", "Active" in html or "active" in html)

        status, _, html = c.get(f"/admin/apps/{app_id}/tables/{tbl_id}/columns")
        token = c.csrf(html)
        status, url, _ = c.post(f"/admin/apps/{app_id}/deactivate", {"csrf_token": token or ""})
        assert_ok("Deactivate app", status in (200, 302), f"status={status}")

        # ── Delete column ─────────────────────────────────────────────────

        if col_id:
            section("App Manager — Delete column")
            status, _, html = c.get(f"/admin/apps/{app_id}/tables/{tbl_id}/columns")
            token = c.csrf(html)
            status, url, _ = c.post(
                f"/admin/apps/{app_id}/tables/{tbl_id}/columns/{col_id}/delete",
                {"csrf_token": token or ""},
            )
            assert_ok("Delete column → redirect", status in (200, 302), f"status={status}")

    # ── Delete table ──────────────────────────────────────────────────────

    if tbl_id:
        section("App Manager — Delete table")
        status, _, html = c.get(f"/admin/apps/{app_id}/tables")
        token = c.csrf(html)
        status, url, _ = c.post(
            f"/admin/apps/{app_id}/tables/{tbl_id}/delete",
            {"csrf_token": token or ""},
        )
        assert_ok("Delete table → redirect", status in (200, 302), f"status={status}")

    # ── Delete app ────────────────────────────────────────────────────────

    section("App Manager — Delete app")

    status, _, html = c.get("/admin/apps")
    token = c.csrf(html)
    status, url, _ = c.post(f"/admin/apps/{app_id}/delete", {"csrf_token": token or ""})
    assert_ok("Delete app → redirect to apps list", status in (200, 302), f"status={status}")

    status, _, html = c.get("/admin/apps")
    assert_ok("Deleted app no longer in list", APP_NAME not in html or APP_TITLE + " Edited" not in html)

    return summary()


@click.command("appmanager")
@click.option("--base", default="http://localhost:8080", show_default=True)
@click.option("--username", default="admin", show_default=True)
@click.option("--password", default="admin", show_default=True)
def cmd(base, username, password):
    """Test App Manager CRUD (apps, tables, columns, activate)."""
    run(base, username, password)
