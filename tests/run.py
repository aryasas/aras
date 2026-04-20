#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/run.py — Web test CLI for Aras.

Usage examples:
  python tests/run.py all --username admin --password admin
  python tests/run.py routes
  python tests/run.py auth   --username admin --password admin
  python tests/run.py admin  --username admin --password admin
  python tests/run.py appmanager
  python tests/run.py builtapp --app-url /inventory/products --field name --value "Widget"
  python tests/run.py all --base http://localhost:5000 --username admin --password secret
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import click
from tests.test_auth       import cmd as auth_cmd
from tests.test_admin      import cmd as admin_cmd
from tests.test_appmanager import cmd as appmanager_cmd
from tests.test_builtapp   import cmd as builtapp_cmd
from tests.test_routes     import cmd as routes_cmd
from tests.test_install    import cmd as install_cmd


@click.group()
def cli():
    """Aras web test CLI — HTTP tests against a running server."""
    pass


cli.add_command(auth_cmd,        name="auth")
cli.add_command(admin_cmd,       name="admin")
cli.add_command(appmanager_cmd,  name="appmanager")
cli.add_command(builtapp_cmd,    name="builtapp")
cli.add_command(routes_cmd,      name="routes")
cli.add_command(install_cmd,     name="install")


@cli.command("all")
@click.option("--base",     default="http://localhost:8080", show_default=True)
@click.option("--username", default="admin",                 show_default=True)
@click.option("--password", default="admin",                 show_default=True)
def all_cmd(base, username, password):
    """Run all test suites."""
    from tests import helpers as h
    from tests.test_routes     import run as run_routes
    from tests.test_auth       import run as run_auth
    from tests.test_admin      import run as run_admin
    from tests.test_appmanager import run as run_appmanager
    from tests.test_install    import run as run_install

    total_failures = 0
    click.echo(f"\n\033[1mAras Web Tests\033[0m  →  {base}\n" + "═" * 54)

    h.reset(); click.echo("\n\033[1m[1/5] Routes\033[0m")
    total_failures += run_routes(base, username, password)

    h.reset(); click.echo("\n\033[1m[2/5] Auth\033[0m")
    total_failures += run_auth(base, username, password)

    h.reset(); click.echo("\n\033[1m[3/5] Admin\033[0m")
    total_failures += run_admin(base, username, password)

    h.reset(); click.echo("\n\033[1m[4/5] App Manager\033[0m")
    total_failures += run_appmanager(base, username, password)

    h.reset(); click.echo("\n\033[1m[5/5] Install/Uninstall\033[0m")
    total_failures += run_install(base, username, password)

    click.echo("\n" + "═" * 54)
    if total_failures == 0:
        click.echo("\033[92m  All suites passed.\033[0m\n")
    else:
        click.echo(f"\033[91m  {total_failures} total failure(s).\033[0m\n")
        sys.exit(1)


if __name__ == "__main__":
    cli()
