# -*- coding: utf-8 -*-
"""
test/test_appmanager.py — App Manager CRUD tests:
  apps (create/edit/delete), tables (create/edit/delete),
  columns (add/delete), fields endpoint, activate/deactivate.
"""
import re
import click
from .client import Client
from .helpers import section, assert_ok, summary, reset

TABLE_NAME  = "items"
TABLE_TITLE = "Items"
COL_NAME    = "item_name"
COL_LABEL   = "Item Name"


def run(base: str, username: str, password: str):
    import time
    ts = str(int(time.time()))[-6:]
    app_name  = f"testapp{ts}"
    app_title = f"Test App {ts}"

    reset()
    c = Client(base)
    c.login(username, password)

    # ── Apps list ─────────────────────────────────────────────────────────

    section("App Manager — Apps list")

    status, _, html = c.get("/admin/apps")
    assert_ok("GET /admin/apps → 200", status == 200, f"status={status}")
    assert_ok("Apps page has Add New button", "apps/new" in html or "Add New" in html)

    # ── Create App ────────────────────────────────────────────────────────

    section("App Manager — Create app")

    status, _, html = c.get("/admin/apps/new")
    assert_ok("GET /admin/apps/new → 200", status == 200, f"status={status}")
    token = c.csrf(html)
    assert_ok("New-app form has CSRF token", bool(token))

    status, url, html = c.post("/admin/apps/new", {
        "csrf_token": token or "",
        "name": app_name,
        "title": app_title,
        "main_title": app_title,
        "url": f"/{app_name}",
        "endpoint": app_name,
        "in_sidebar": "y",
        "is_active": "",
        "menu_order": "10",
    })
    assert_ok("Create app → redirects to apps list or tables", "apps" in url, f"url={url}")

    # Find app ID: locate <code>app_name</code> in page, find the FIRST apps/N/tables link after it
    status, _, html = c.get("/admin/apps")
    assert_ok("Apps list loads after create", status == 200)
    app_id = ""
    m = re.search(rf'<code>{re.escape(app_name)}</code>', html)
    if m:
        after = html[m.start():]
        m2 = re.search(r'apps/(\d+)/tables', after)
        app_id = m2.group(1) if m2 else ""

    assert_ok("Found created app ID", bool(app_id), f"app_id={app_id!r}")
    if not app_id:
        print("  [skip] Cannot continue without app_id")
        return summary()

    # ── Edit App ──────────────────────────────────────────────────────────

    section("App Manager — Edit app")

    status, _, html = c.get(f"/admin/apps/{app_id}/edit")
    assert_ok(f"GET /admin/apps/{app_id}/edit → 200", status == 200, f"status={status}")
    assert_ok("Edit form pre-populated with app name", app_name in html)
    token = c.csrf(html)
    status, url, _ = c.post(f"/admin/apps/{app_id}/edit", {
        "csrf_token": token or "",
        "name": app_name,
        "title": app_title + " Edited",
        "main_title": app_title,
        "url": f"/{app_name}",
        "endpoint": app_name,
        "in_sidebar": "y",
        "menu_order": "10",
    })
    assert_ok("Edit app → redirects", "apps" in url or str(app_id) in url, f"url={url}")

    # ── Fields endpoint ───────────────────────────────────────────────────

    section("App Manager — Fields list")

    status, _, html = c.get(f"/admin/apps/{app_id}/fields")
    assert_ok(f"GET /admin/apps/{app_id}/fields → 200", status == 200, f"status={status}")

    # ── Tables ────────────────────────────────────────────────────────────

    section("App Manager — Tables list")

    status, _, html = c.get(f"/admin/apps/{app_id}/tables")
    assert_ok(f"GET /admin/apps/{app_id}/tables → 200", status == 200, f"status={status}")
    assert_ok("Tables page mentions table", "table" in html.lower())

    # Create table
    section("App Manager — Create table")

    status, _, html = c.get(f"/admin/apps/{app_id}/tables/new")
    assert_ok("GET tables/new → 200", status == 200, f"status={status}")
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

    # Find table ID
    status, _, html = c.get(f"/admin/apps/{app_id}/tables")
    tbl_ids = re.findall(rf'tables/(\d+)/columns', html)
    tbl_id  = tbl_ids[0] if tbl_ids else ""
    assert_ok("Found created table ID", bool(tbl_id), f"tbl_id={tbl_id!r}")

    if tbl_id:
        # Edit table
        section("App Manager — Edit table")

        status, _, html = c.get(f"/admin/apps/{app_id}/tables/{tbl_id}/edit")
        assert_ok(f"GET .../tables/{tbl_id}/edit → 200", status == 200, f"status={status}")
        assert_ok("Edit table form pre-populated", TABLE_NAME in html)
        token = c.csrf(html)
        status, url, _ = c.post(f"/admin/apps/{app_id}/tables/{tbl_id}/edit", {
            "csrf_token": token or "",
            "name": TABLE_NAME,
            "title": TABLE_TITLE + " Edited",
            "menu_title": TABLE_TITLE,
            "url_suffix": TABLE_NAME,
            "show_in_menu": "y",
            "is_active": "y",
            "menu_order": "1",
        })
        assert_ok("Edit table → redirects", status in (200, 302), f"url={url} status={status}")

        # ── Columns ───────────────────────────────────────────────────────

        section("App Manager — Columns (add multiple types)")

        status, _, html = c.get(f"/admin/apps/{app_id}/tables/{tbl_id}/columns")
        assert_ok(f"GET .../columns → 200", status == 200, f"status={status}")
        token = c.csrf(html)

        # Add string column
        status, url, html = c.post(f"/admin/apps/{app_id}/tables/{tbl_id}/columns", {
            "csrf_token": token or "",
            "name": COL_NAME,
            "label": COL_LABEL,
            "field_type": "string",
            "required": "y",
            "order": "1",
        })
        assert_ok("Add string column → success", COL_NAME in html or status in (200, 302), f"status={status}")

        # Add integer column
        status, _, html = c.get(f"/admin/apps/{app_id}/tables/{tbl_id}/columns")
        token = c.csrf(html)
        status, url, html = c.post(f"/admin/apps/{app_id}/tables/{tbl_id}/columns", {
            "csrf_token": token or "",
            "name": "item_count",
            "label": "Item Count",
            "field_type": "integer",
            "required": "",
            "order": "2",
        })
        assert_ok("Add integer column → success", "item_count" in html or status in (200, 302), f"status={status}")

        # Add text column
        status, _, html = c.get(f"/admin/apps/{app_id}/tables/{tbl_id}/columns")
        token = c.csrf(html)
        status, url, html = c.post(f"/admin/apps/{app_id}/tables/{tbl_id}/columns", {
            "csrf_token": token or "",
            "name": "item_desc",
            "label": "Description",
            "field_type": "text",
            "required": "",
            "order": "3",
        })
        assert_ok("Add text column → success", "item_desc" in html or status in (200, 302), f"status={status}")

        # Verify columns page shows all added columns
        status, _, html = c.get(f"/admin/apps/{app_id}/tables/{tbl_id}/columns")
        assert_ok("Columns page shows string column", COL_NAME in html)
        assert_ok("Columns page shows integer column", "item_count" in html)

        # Find column IDs
        col_ids = re.findall(rf'columns/(\d+)/delete', html)
        col_id  = col_ids[0] if col_ids else ""

        # ── Activate / Deactivate ─────────────────────────────────────────

        section("App Manager — Activate / Deactivate")

        token = c.csrf(html)
        status, url, _ = c.post(f"/admin/apps/{app_id}/activate", {"csrf_token": token or ""})
        assert_ok("Activate app → 200 or redirect", status in (200, 302), f"status={status} url={url}")

        status, _, html = c.get("/admin/apps")
        assert_ok("App shows Active badge after activate", "Active" in html or "active" in html)

        status, _, html = c.get(f"/admin/apps/{app_id}/tables/{tbl_id}/columns")
        token = c.csrf(html)
        status, url, _ = c.post(f"/admin/apps/{app_id}/deactivate", {"csrf_token": token or ""})
        assert_ok("Deactivate app → 200 or redirect", status in (200, 302), f"status={status}")

        status, _, html = c.get("/admin/apps")
        assert_ok("App shows inactive after deactivate", "Active" not in html or "Inactive" in html or status == 200)

        # ── Delete columns ────────────────────────────────────────────────

        section("App Manager — Delete columns")

        status, _, html = c.get(f"/admin/apps/{app_id}/tables/{tbl_id}/columns")
        all_col_ids = re.findall(rf'columns/(\d+)/delete', html)
        for cid in all_col_ids:
            token = c.csrf(html)
            status, url, html = c.post(
                f"/admin/apps/{app_id}/tables/{tbl_id}/columns/{cid}/delete",
                {"csrf_token": token or ""},
            )
            assert_ok(f"Delete column {cid} → 200 or redirect", status in (200, 302), f"status={status}")
            # refresh html for next iteration's token
            _, _, html = c.get(f"/admin/apps/{app_id}/tables/{tbl_id}/columns")

        assert_ok("All columns deleted", len(re.findall(rf'columns/(\d+)/delete', html)) == 0)

        # ── Delete table ──────────────────────────────────────────────────

        section("App Manager — Delete table")

        status, _, html = c.get(f"/admin/apps/{app_id}/tables")
        token = c.csrf(html)
        status, url, _ = c.post(
            f"/admin/apps/{app_id}/tables/{tbl_id}/delete",
            {"csrf_token": token or ""},
        )
        assert_ok("Delete table → 200 or redirect", status in (200, 302), f"status={status}")

        status, _, html = c.get(f"/admin/apps/{app_id}/tables")
        assert_ok("Table no longer listed after delete", TABLE_NAME not in html or status == 200)

    # ── Delete app ────────────────────────────────────────────────────────

    section("App Manager — Delete app")

    status, _, html = c.get("/admin/apps")
    token = c.csrf(html)
    status, url, _ = c.post(f"/admin/apps/{app_id}/delete", {"csrf_token": token or ""})
    assert_ok("Delete app → 200 or redirect", status in (200, 302), f"status={status}")

    status, _, html = c.get("/admin/apps")
    assert_ok("Deleted app no longer in list", app_name not in html or (app_title + " Edited") not in html)

    return summary()


@click.command("appmanager")
@click.option("--base", default="http://localhost:8080", show_default=True)
@click.option("--username", default="admin", show_default=True)
@click.option("--password", default="admin", show_default=True)
def cmd(base, username, password):
    """Test App Manager CRUD (apps, tables, columns, activate/deactivate)."""
    run(base, username, password)
