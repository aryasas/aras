# -*- coding: utf-8 -*-
"""
arasCore/lib/bin.py
===================
Top-level `aras` shell entrypoint (ERPNext-like).

Usage:
    aras install-app <name_or_file> [--activate]
    aras list-apps
    aras activate-app <name>
    aras deactivate-app <name>
    aras uninstall-app <name> [--drop-tables]
    aras export-app <name> [--format yaml|json] [--output FILE]
    aras new-app <name>

Under the hood this delegates to the Flask CLI `flask aras <command>` so every
command runs inside an app context.

Hook this via setup.py / pyproject.toml:
    entry_points={"console_scripts": ["aras = arasCore.lib.bin:main"]}
"""
import os
import sys


def main():
    # Ensure project root on sys.path
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(here))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    os.environ.setdefault("FLASK_APP", "run:app")

    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        _print_help()
        return 0

    # Delegate to Flask CLI: `flask aras <cmd> <args…>`
    from flask.cli import main as flask_main
    sys.argv = ["flask", "aras", *argv]
    return flask_main()


def _print_help():
    print("""aras — Aras Framework CLI

Usage:
  aras install-app <name_or_file> [--activate]
  aras list-apps
  aras activate-app <name>
  aras deactivate-app <name>
  aras uninstall-app <name> [--drop-tables]
  aras export-app <name> [--format yaml|json] [--output FILE]
  aras new-app <name> [--title TITLE]

Other:
  aras csu                  Create a superuser
  aras reset --username X   Reset a user's password
  aras erp-init             Seed ERP core data
  aras dbtest               Test DB connection
  aras dbca                 Create all tables

Run `aras <command> --help` for per-command options.
""")


if __name__ == "__main__":
    sys.exit(main() or 0)
