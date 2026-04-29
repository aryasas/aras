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
        from aras.erp.cli import register_erp_commands
        register_erp_commands(aras)
    except (ImportError, Exception):
        pass

    app.cli.add_command(aras)
