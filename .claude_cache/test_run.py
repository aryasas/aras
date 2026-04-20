#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test/run.py — Web test CLI for Aras.

Usage examples:
  # Run all tests
  python test/run.py all --username admin --password admin

  # Individual suites
  python test/run.py routes
  python test/run.py auth   --username admin --password admin
  python test/run.py admin  --username admin --password admin
  python test/run.py appmanager

  # Test a specific live built app (must already be active)
  python test/run.py builtapp --app-url /inventory/products --field name --value "Widget"

  # Different base URL
  python test/run.py all --base http://localhost:5000 --username admin --password secret
"""
import sys
import os

# Allow running as: python test/run.py  (from project root)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import click
from test.test_auth       import cmd as auth_cmd
from test.test_admin      import cmd as admin_cmd
from test.test_appbuilder import cmd as appbuilder_cmd
from test.test_builtapp   import cmd as builtapp_cmd
from test.test_routes     import cmd as routes_cmd


@click.group()
def cli():
    """Aras web test CLI — HTTP tests against a running server."""
    pass


# Register individual commands
cli.add_command(auth_cmd,        name="auth")
cli.add_command(admin_cmd,       name="admin")
cli.add_command(appbuilder_cmd,  name="appmanager")
cli.add_command(builtapp_cmd,    name="builtapp")
cli.add_command(routes_cmd,      name="routes")


@cli.command("all")
@click.option("--base",     default="http://localhost:8080", show_default=True, help="Base URL of the running server")
@click.option("--username", default="admin", show_default=True, help="Admin username or email")
@click.option("--password", default="admin", show_default=True, help="Admin password")
def all_cmd(base, username, password):
    """Run all test suites (routes + auth + admin + appmanager)."""
    from test import helpers as h
    from test.test_routes     import run as run_routes
    from test.test_auth       import run as run_auth
    from test.test_admin      import run as run_admin
    from test.test_appbuilder import run as run_appbuilder

    total_failures = 0

    click.echo(f"\n\033[1mAras Web Tests\033[0m  →  {base}\n" + "═" * 54)

    h.reset()
    click.echo("\n\033[1m[1/4] Routes\033[0m")
    total_failures += run_routes(base, username, password)

    h.reset()
    click.echo("\n\033[1m[2/4] Auth\033[0m")
    total_failures += run_auth(base, username, password)

    h.reset()
    click.echo("\n\033[1m[3/4] Admin\033[0m")
    total_failures += run_admin(base, username, password)

    h.reset()
    click.echo("\n\033[1m[4/4] App Manager\033[0m")
    total_failures += run_appbuilder(base, username, password)

    click.echo("\n" + "═" * 54)
    if total_failures == 0:
        click.echo("\033[92m  All suites passed.\033[0m\n")
    else:
        click.echo(f"\033[91m  {total_failures} total failure(s).\033[0m\n")
        sys.exit(1)


if __name__ == "__main__":
    cli()
