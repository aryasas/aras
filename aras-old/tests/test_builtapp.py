# -*- coding: utf-8 -*-
"""
test/test_builtapp.py — CRUD tests for a live built app (web + admin views + API).

Requires a built, active app to already exist.
Pass --app-url (the app's base URL, e.g. /inventory/products)
and --field/--value for the first required field to create a test record.

Example:
  python test/run.py builtapp --app-url /inventory/products --field name --value "Test Item"
"""
import re
import json
import click
from .client import Client
from .helpers import section, assert_ok, summary, reset


def run(base: str, username: str, password: str, app_url: str, field: str, value: str):
    reset()
    c = Client(base)

    # Strip trailing slash
    app_url = "/" + app_url.strip("/")
    adm_url = "/admin" + app_url

    # ── Web routes (public read) ──────────────────────────────────────────

    section(f"Built App — Web list  {app_url}/")

    status, url, html = c.get(f"{app_url}/")
    assert_ok(f"GET {app_url}/ → 200", status == 200, f"status={status}")
    assert_ok("Web list uses web template (no base_index)", "base_index" not in html)

    section(f"Built App — Web add (requires login)")

    status, url, _ = c.get(f"{app_url}/add/")
    assert_ok(f"GET {app_url}/add/ unauthenticated → redirect to login", "login" in url, f"url={url}")

    c.login(username, password)

    status, url, html = c.get(f"{app_url}/add/")
    assert_ok(f"GET {app_url}/add/ authenticated → 200", status == 200, f"status={status}")
    assert_ok("Web add form has CSRF token", 'csrf_token' in html)

    # Create a record via web form
    token = c.csrf(html)
    post_data = {"csrf_token": token or "", field: value}
    status, url, html = c.post(f"{app_url}/add/", post_data)
    assert_ok("POST web add → redirect to list", app_url in url or status == 302, f"url={url} status={status}")

    # Get record id from list
    status, _, html = c.get(f"{app_url}/")
    ids = re.findall(rf'{re.escape(app_url)}/(\d+)/', html)
    record_id = ids[0] if ids else ""
    assert_ok("Record appears in web list after add", bool(record_id) or value in html, f"record_id={record_id!r}")

    # ── Web edit ──────────────────────────────────────────────────────────

    if record_id:
        section(f"Built App — Web edit {app_url}/{record_id}/")

        status, _, html = c.get(f"{app_url}/{record_id}/")
        assert_ok(f"GET {app_url}/{record_id}/ → 200", status == 200, f"status={status}")
        token = c.csrf(html)
        updated_value = value + "_edited"
        status, url, _ = c.post(f"{app_url}/{record_id}/", {
            "csrf_token": token or "",
            field: updated_value,
        })
        assert_ok("POST web edit → redirect", app_url in url or status == 302, f"url={url}")

    # ── Admin routes ──────────────────────────────────────────────────────

    section(f"Built App — Admin list  {adm_url}/")

    status, _, html = c.get(f"{adm_url}/")
    assert_ok(f"GET {adm_url}/ → 200", status == 200, f"status={status}")
    assert_ok("Admin list uses admin template", any(k in html for k in ["base_index", "sidebar", "admin/ab_list"]))

    section(f"Built App — Admin add  {adm_url}/add/")

    status, _, html = c.get(f"{adm_url}/add/")
    assert_ok(f"GET {adm_url}/add/ → 200", status == 200, f"status={status}")
    token = c.csrf(html)
    status, url, html = c.post(f"{adm_url}/add/", {
        "csrf_token": token or "",
        field: value + "_via_admin",
    })
    assert_ok("POST admin add → redirect", adm_url in url or status == 302, f"url={url}")

    # Find admin record
    status, _, html = c.get(f"{adm_url}/")
    adm_ids = re.findall(rf'{re.escape(adm_url)}/(\d+)/', html)
    adm_record_id = adm_ids[0] if adm_ids else ""
    assert_ok("Record in admin list after add", bool(adm_record_id) or (value + "_via_admin") in html)

    if adm_record_id:
        section(f"Built App — Admin edit  {adm_url}/{adm_record_id}/")

        status, _, html = c.get(f"{adm_url}/{adm_record_id}/")
        assert_ok(f"GET {adm_url}/{adm_record_id}/ → 200", status == 200, f"status={status}")
        token = c.csrf(html)
        status, url, _ = c.post(f"{adm_url}/{adm_record_id}/", {
            "csrf_token": token or "",
            field: value + "_adm_edited",
        })
        assert_ok("POST admin edit → redirect", adm_url in url or status == 302, f"url={url}")

        # Admin delete
        section(f"Built App — Admin delete  {adm_url}/{adm_record_id}/delete/")

        status, _, html = c.get(f"{adm_url}/")
        token = c.csrf(html)
        status, url, _ = c.post(f"{adm_url}/{adm_record_id}/delete/", {"csrf_token": token or ""})
        assert_ok("Admin delete → redirect", adm_url in url or status in (200, 302), f"url={url}")

    # ── API routes ────────────────────────────────────────────────────────

    section(f"Built App — API  /api{app_url}/")

    # GET list
    status, body = c.request_json("GET", f"/api{app_url}/")
    assert_ok(f"GET /api{app_url}/ → 200", status == 200, f"status={status}")
    try:
        items = json.loads(body)
        assert_ok("API list returns JSON array", isinstance(items, list), f"type={type(items)}")
    except Exception:
        assert_ok("API list returns valid JSON", False, f"body[:80]={body[:80]}")
        items = []

    # POST create
    status, body = c.request_json("POST", f"/api{app_url}/", {field: value + "_api"})
    assert_ok(f"POST /api{app_url}/ → 201", status == 201, f"status={status}")
    try:
        created = json.loads(body)
        api_id  = created.get("id", "")
    except Exception:
        api_id = ""
    assert_ok("API create returns record with id", bool(api_id), f"body={body[:80]}")

    if api_id:
        # GET single
        status, body = c.request_json("GET", f"/api{app_url}/{api_id}/")
        assert_ok(f"GET /api{app_url}/{api_id}/ → 200", status == 200, f"status={status}")

        # PUT update
        status, body = c.request_json("PUT", f"/api{app_url}/{api_id}/", {field: value + "_api_updated"})
        assert_ok(f"PUT /api{app_url}/{api_id}/ → 200", status == 200, f"status={status}")

        # DELETE
        status, body = c.request_json("DELETE", f"/api{app_url}/{api_id}/")
        assert_ok(f"DELETE /api{app_url}/{api_id}/ → 200", status == 200, f"status={status}")

    # ── Web delete (cleanup) ──────────────────────────────────────────────

    if record_id:
        section("Built App — Web delete (cleanup)")

        status, _, html = c.get(f"{app_url}/")
        token = c.csrf(html)
        status, url, _ = c.post(f"{app_url}/{record_id}/delete/", {"csrf_token": token or ""})
        assert_ok("Web delete record → redirect", app_url in url or status in (200, 302), f"url={url}")

    return summary()


@click.command("builtapp")
@click.option("--base",     default="http://localhost:8080", show_default=True)
@click.option("--username", default="admin",  show_default=True)
@click.option("--password", default="admin",  show_default=True)
@click.option("--app-url",  default="",  required=True, help="App URL prefix, e.g. /inventory/products")
@click.option("--field",    default="name",  show_default=True, help="Field name for test record")
@click.option("--value",    default="TestRecord", show_default=True, help="Value for that field")
def cmd(base, username, password, app_url, field, value):
    """Test a live built app: web view, admin view, and API CRUD."""
    run(base, username, password, app_url, field, value)
