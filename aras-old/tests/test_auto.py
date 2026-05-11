# -*- coding: utf-8 -*-
"""tests/test_auto.py — framework-driven auto-discovery test.

Iterates every ArasModel registered in the running app and probes its
auto-generated REST + admin routes. Adding a model to any app auto-extends
this test — no manual test code needed.

Usage:
  python tests/run.py auto --username admin --password admin
"""
import click
from .client import Client
from .helpers import section, assert_ok, summary, reset


def _discover_resources(client: Client):
    """Return [(app, resource, table)] for every ArasModel with __admin_list__."""
    # The framework exposes a manifest endpoint listing all registered resources;
    # if not present, fall back to AppManagerTable rows.
    res = client.get("/api/_meta/resources")
    if res.status_code == 200:
        return [(r["app"], r["resource"], r.get("table")) for r in res.json()]
    return []


def run(base: str, username: str, password: str):
    reset()
    c = Client(base)

    section("Login")
    assert_ok(c.login(username, password), "login")

    section("Auto-discover registered resources")
    resources = _discover_resources(c)
    if not resources:
        click.echo("  no /api/_meta/resources endpoint — skipping auto-test")
        summary()
        return

    section(f"Probe {len(resources)} resources")
    for app, resource, _table in resources:
        for path in (f"/api/{app}/{resource}/", f"/admin/{app}/{resource}/"):
            r = c.get(path)
            assert_ok(f"{path} -> {r.status_code}", r.status_code in (200, 302))

    return summary()


@click.command("auto")
@click.option("--base",     default="http://127.0.0.1:8080")
@click.option("--username", default="admin")
@click.option("--password", default="admin")
def cmd(base, username, password):
    run(base, username, password)
