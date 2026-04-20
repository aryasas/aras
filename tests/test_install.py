# -*- coding: utf-8 -*-
"""
tests/test_install.py — Install / uninstall cycle tests.

Covers 3 install methods using pre-generated fixture files:
  1. YAML  (.yaml)  → tests/fixtures/test_app_yaml.yaml   → app: test_yaml_app
  2. YML   (.yml)   → tests/fixtures/test_app_yml.yml     → app: test_yml_app
  3. JSON  (.json)  → tests/fixtures/test_app_json.json   → app: test_json_app

Each cycle:
  a) Ensure app is absent (delete if present from a previous run)
  b) Install via file upload to /admin/apps/install
  c) Verify app appears in /admin/apps
  d) Activate app
  e) Seed 1 row via the built-app API  POST /api/<app>/<table>/
  f) Verify row via GET /api/<app>/<table>/
  g) Delete app (uninstall)
  h) Verify app is gone
"""
import os
import re
import json
import click

from .client import Client
from .helpers import section, assert_ok, summary, reset

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

# fixture_file, app_name, table_name, seed_payload
INSTALL_CASES = [
    (
        "test_app_yaml.yaml",
        "test_yaml_app",
        "products",
        {"name": "Sample Product", "price": "9.99", "notes": "Seeded by test"},
    ),
    (
        "test_app_yml.yml",
        "test_yml_app",
        "tasks",
        {"title": "Sample Task", "status": "open"},
    ),
    (
        "test_app_json.json",
        "test_json_app",
        "contacts",
        {"full_name": "John Doe", "email": "john@example.com", "phone": "555-1234"},
    ),
]


def _find_app_id(html: str, app_name: str) -> str:
    m = re.search(rf'<code>{re.escape(app_name)}</code>', html)
    if not m:
        return ""
    after = html[m.start():]
    m2 = re.search(r'apps/(\d+)/tables', after)
    return m2.group(1) if m2 else ""


def _delete_app_if_present(c: Client, app_name: str):
    status, _, html = c.get("/admin/apps")
    app_id = _find_app_id(html, app_name)
    if not app_id:
        return
    token = c.csrf(html)
    c.post(f"/admin/apps/{app_id}/delete", {"csrf_token": token or ""})


def _run_case(c: Client, fixture_file: str, app_name: str, table_name: str, seed: dict):
    fixture_path = os.path.join(FIXTURES_DIR, fixture_file)
    ext = fixture_file.rsplit(".", 1)[-1].lower()
    content_type = "application/json" if ext == "json" else "application/x-yaml"

    section(f"Install — cleanup: {app_name}")
    _delete_app_if_present(c, app_name)
    status, _, html = c.get("/admin/apps")
    assert_ok(f"App {app_name} absent before install", app_name not in html, f"still found {app_name}")

    section(f"Install — upload {fixture_file}")
    status, _, html = c.get("/admin/apps/install")
    assert_ok("GET /admin/apps/install → 200", status == 200, f"status={status}")
    token = c.csrf(html)

    with open(fixture_path, "rb") as fh:
        file_bytes = fh.read()

    status, url, html = c.post_multipart(
        "/admin/apps/install",
        fields={"csrf_token": token or "", "install_type": "definition"},
        files={"definition_file": (fixture_file, file_bytes, content_type)},
    )
    assert_ok(
        f"Install {fixture_file} → redirect to tables or apps",
        "tables" in url or "apps" in url or status in (200, 302),
        f"url={url} status={status}",
    )

    section(f"Install — verify {app_name} in app list")
    status, _, html = c.get("/admin/apps")
    assert_ok("Apps list → 200", status == 200)
    app_id = _find_app_id(html, app_name)
    assert_ok(f"Found app_id for {app_name}", bool(app_id), f"app_id={app_id!r}")
    if not app_id:
        return

    section(f"Install — activate {app_name}")
    status, _, html = c.get("/admin/apps")
    token = c.csrf(html)
    status, url, _ = c.post(f"/admin/apps/{app_id}/activate", {"csrf_token": token or ""})
    assert_ok(f"Activate {app_name} → 200 or redirect", status in (200, 302), f"status={status}")

    section(f"Install — seed 1 row via API: {table_name}")
    status, _, body = c.post_json(f"/api/{app_name}/{table_name}/", seed)
    assert_ok(
        f"POST /api/{app_name}/{table_name}/ → 200/201",
        status in (200, 201),
        f"status={status} body={body[:200]}",
    )
    try:
        resp = json.loads(body)
        row_id = (resp.get("data") or {}).get("id") or (resp.get("id"))
    except Exception:
        row_id = None
    assert_ok(f"Seed response has data", bool(body), f"body={body[:100]}")

    section(f"Install — verify row via API GET: {table_name}")
    status, _, body = c.request_json("GET", f"/api/{app_name}/{table_name}/")
    assert_ok(
        f"GET /api/{app_name}/{table_name}/ → 200",
        status == 200,
        f"status={status}",
    )

    section(f"Install — uninstall {app_name}")
    status, _, html = c.get("/admin/apps")
    token = c.csrf(html)
    status, url, _ = c.post(f"/admin/apps/{app_id}/delete", {"csrf_token": token or ""})
    assert_ok(f"Delete {app_name} → 200 or redirect", status in (200, 302), f"status={status}")

    status, _, html = c.get("/admin/apps")
    assert_ok(f"{app_name} gone after uninstall", app_name not in html, f"still found in {url}")


def run(base: str, username: str, password: str):
    reset()
    c = Client(base)
    c.login(username, password)

    for fixture_file, app_name, table_name, seed in INSTALL_CASES:
        _run_case(c, fixture_file, app_name, table_name, seed)

    return summary()


@click.command("install")
@click.option("--base",     default="http://localhost:8080", show_default=True)
@click.option("--username", default="admin",                 show_default=True)
@click.option("--password", default="admin",                 show_default=True)
def cmd(base, username, password):
    """Test install/uninstall cycle for YAML, YML, and JSON fixture files."""
    run(base, username, password)
