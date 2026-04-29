import os
import click

def register_misc_commands(aras):
    @aras.command()
    def filldata():
        """Fill Test Data (not implemented)."""
        click.echo("filldata: no seed data defined yet.")

    @aras.command()
    @click.option("--count", default=1, help="number of greetings")
    @click.argument("name")
    def hello(count, name):
        """This script prints hello NAME COUNT times."""
        for x in range(count):
            click.echo(f"Hello {name}!")

    @aras.command("erp-init", help="Run ERP seed + migrate (idempotent)")
    def erp_init():
        """Run ERP DB migrations and seed core data."""
        from aras.erp.erp_core.seed import run_seed
        from aras.erp.erp_core.migrate_task4 import run as mt4
        from aras.erp.erp_core.migrate_task5 import run as mt5
        from aras.erp.erp_core.migrate_task6 import run as mt6
        import flask
        _app = flask.current_app._get_current_object()
        mt4(_app)
        mt5(_app)
        mt6(_app)
        run_seed(_app)
        click.echo("[erp-init] done.")

    @aras.command("dev-mode", help="Switch between development and production mode")
    @click.option("--set", "mode_val", type=click.Choice(["0", "1"]),
                  required=True, help="1 = development, 0 = production")
    def dev_mode(mode_val):
        import json as _json
        import flask
        _app = flask.current_app._get_current_object()
        instance_dir = _app.instance_path
        os.makedirs(instance_dir, exist_ok=True)
        mode_file = os.path.join(instance_dir, "mode.json")
        is_dev = mode_val == "1"
        data = {"mode": "development" if is_dev else "production"}
        with open(mode_file, "w") as f:
            _json.dump(data, f)
        label = "DEVELOPMENT" if is_dev else "PRODUCTION"
        click.echo(f"[dev-mode] switched to {label}. Restart server to apply.")
