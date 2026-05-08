import click
from .cli_db import register_db_commands
from .cli_auth import register_auth_commands
from .cli_app import register_app_commands
from .cli_report import register_report_commands
from .cli_test import register_test_commands
from .cli_misc import register_misc_commands
from .ai_context import register_ai_commands

def register_cli(app):
    @app.cli.group()
    def aras():
        """Aras Framework CLI."""
        pass

    # Register grouped commands
    register_db_commands(aras)
    register_auth_commands(aras)
    register_app_commands(aras)
    register_report_commands(aras)
    register_test_commands(aras)
    register_misc_commands(aras)
    register_ai_commands(aras)

    try:
        from app.erp.cli import register_erp_commands
        register_erp_commands(aras)
    except (ImportError, Exception):
        pass

    # Auto-register @action-decorated CLI commands. Service modules were imported at
    # blueprint registration time; commands grouped per app name.
    try:
        _register_action_commands(aras)
    except Exception:
        import logging
        logging.getLogger(__name__).warning("[cli] action discovery failed", exc_info=True)

    app.cli.add_command(aras)


def _register_action_commands(aras):
    """Discover @action-decorated functions and mount them as CLI subcommands.

    Layout: flask aras <app> <module>.<file>.<func> [--args]
    """
    from arasCore.lib.core.action import get_actions, make_cli_command
    by_group: dict = {}
    for meta in get_actions():
        if meta.http_only:
            continue
        by_group.setdefault(meta.cli_group or "misc", []).append(meta)

    existing_groups = {c.name: c for c in aras.commands.values() if isinstance(c, click.Group)}

    for group_name, metas in by_group.items():
        grp = existing_groups.get(group_name)
        if grp is None:
            grp = click.Group(group_name, help=f"{group_name} actions")
            aras.add_command(grp)
        for meta in metas:
            cmd = make_cli_command(meta)
            grp.add_command(cmd)
