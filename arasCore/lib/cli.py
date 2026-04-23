import os
import sys
import click
import mariadb
from arasCore.lib.database import db_init, db_createall
from arasCore.lib.extensions import db


def db_conn():
    """Test MariaDB connection directly."""
    try:
        conn = mariadb.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            database=os.getenv("DB_NAME"),
        )
        if conn.cursor():
            print("Connection to database OK")
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)


def register_cli(app):
    @app.cli.group()
    def aras():
        """Aras CLI."""
        pass

    app.cli.add_command(aras)

    @aras.command()
    def dbtest():
        """Test DB Connection."""
        db_conn()

    @aras.command()
    def dbinit():
        db_init()

    @aras.command()
    def dbca():
        """Create All Table"""
        db_createall()

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

    @aras.command("csu", help="Create a user with Admin role on database")
    @click.option("--username", prompt="User name")
    @click.option("--email", prompt="User email")
    @click.option(
        "--password",
        prompt="User password",
        hide_input="True",
        confirmation_prompt=True,
    )
    def csu(username, email, password):
        """Install a default admin user."""
        from arasCore.auth import User, create_user
        if User.query.filter_by(email=email).first():
            click.echo("Email already exists.")
            return
        u = create_user(username, email, password, is_admin=True)
        click.echo(f"Created admin user: {u.username}")

    @aras.command("reset", help="Reset Password")
    @click.option("--username", prompt="User name")
    @click.option(
        "--password",
        prompt="New password",
        hide_input="True",
    )
    def reset(username, password):
        """Reset a user password"""
        from arasCore.auth import User
        from arasCore.lib.extensions import db as core_db
        try:
            user = User.query.filter_by(username=username).first()
            if not user:
                click.echo("User not found.")
                return
            user.set_password(password)
            core_db.session.commit()
            click.echo("Password reset successfully.")
        except Exception as e:
            click.echo(f"Error: {e}")

    @aras.command("migrate", help="Run arasCore idempotent migrations (page type, settings, etc.)")
    def migrate():
        import flask
        from arasCore.lib.migrations import m001_page_type, m002_rbac, m004_arasmodel_audit_cols, m005_list_view_setting
        _app = flask.current_app._get_current_object()
        m001_page_type.run(_app)
        m002_rbac.run(_app)
        m004_arasmodel_audit_cols.run(_app)
        m005_list_view_setting.run(_app)
        click.echo("[migrate] done.")

    @aras.command("remigrate", help="Drop & recreate all tables, run all migrations, sync all manifests, seed ERP")
    @click.option("--yes", is_flag=True, default=False, help="Skip confirmation prompt")
    def remigrate(yes):
        """Full remigrate: db_createall → all arasCore migrations → sync all manifests → ERP seed."""
        import flask
        _app = flask.current_app._get_current_object()

        if not yes:
            click.confirm(
                "This will run db.create_all() and all migrations. Continue?",
                abort=True,
            )

        # 1. Create all tables (idempotent — skips existing)
        click.echo("[remigrate] 1/4  db.create_all() ...")
        with _app.app_context():
            db.create_all()

        # 2. arasCore migrations
        click.echo("[remigrate] 2/4  arasCore migrations ...")
        from arasCore.lib.migrations import m001_page_type, m002_rbac, m004_arasmodel_audit_cols, m005_list_view_setting
        m001_page_type.run(_app)
        m002_rbac.run(_app)
        m004_arasmodel_audit_cols.run(_app)
        m005_list_view_setting.run(_app)

        # 3. Sync all code-based manifests → mgr_table/mgr_column
        click.echo("[remigrate] 3/4  sync all manifests ...")
        from arasCore.lib.blueprints import get_helper_registry
        from arasCore.lib.installer import sync_helper_to_db
        registry = get_helper_registry()
        for slug, helper in registry.items():
            try:
                _, stats = sync_helper_to_db(helper, db, _app)
                click.echo(f"          synced '{slug}': "
                           f"+{stats['tables_new']} tables, +{stats['cols_new']} cols")
            except Exception as e:
                click.echo(f"          ERROR syncing '{slug}': {e}")

        # 4. ERP migrations + seed (if app_erp is present)
        click.echo("[remigrate] 4/4  ERP migrations + seed (if installed) ...")
        try:
            from aras.app_erp.erp_core.migrate_task4 import run as mt4
            from aras.app_erp.erp_core.migrate_task5 import run as mt5
            from aras.app_erp.erp_core.migrate_task6 import run as mt6
            from aras.app_erp.erp_core.seed import run_seed
            mt4(_app)
            mt5(_app)
            mt6(_app)
            run_seed(_app)
            click.echo("          ERP done.")
        except ModuleNotFoundError:
            click.echo("          app_erp not installed — skipped.")

        click.echo("[remigrate] all done.")

    @aras.command("erp-init", help="Run ERP seed + migrate (idempotent)")
    def erp_init():
        """Run ERP DB migrations and seed core data."""
        from aras.app_erp.erp_core.seed import run_seed
        from aras.app_erp.erp_core.migrate_task4 import run as migrate_task4
        from aras.app_erp.erp_core.migrate_task5 import run as migrate_task5
        from aras.app_erp.erp_core.migrate_task6 import run as migrate_task6
        import flask
        _app = flask.current_app._get_current_object()
        migrate_task4(_app)
        migrate_task5(_app)
        migrate_task6(_app)
        run_seed(_app)
        click.echo("[erp-init] done.")

    # ── App lifecycle commands (ERPNext-style) ────────────────────────────────

    @aras.command("install-app", help="Install an app from YAML/JSON or Python manifest")
    @click.argument("app_name_or_file")
    @click.option("--activate", is_flag=True, default=False,
                  help="Activate immediately after install (creates DB tables)")
    def install_app(app_name_or_file, activate):
        """
        Install an app from a YAML/JSON file OR a Python manifest (AppHelper).

        `app_name_or_file` can be:
          - path to a definition file: `aras install-app ./my_app.yaml`
          - app name — tries YAML first, then Python manifest:
              ./<name>.yaml | aras/app_<name>/manifest.yaml
              aras/app_<name>/manifest.py  (AppHelper)
        """
        import yaml, json as _json
        import flask
        from arasCore.lib.installer import install_from_definition, parse_app_definition, sync_helper_to_db

        _app = flask.current_app._get_current_object()

        # ── Try YAML/JSON path first ──────────────────────────────────────────
        path = _resolve_install_path(app_name_or_file, _app)
        if path:
            click.echo(f"[install-app] source: {path}")
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read()
            data = yaml.safe_load(raw) if path.lower().endswith((".yaml", ".yml")) else _json.loads(raw)
            try:
                definition = parse_app_definition(data)
                app_obj    = install_from_definition(definition, db, _app)
                click.echo(f"[install-app] installed '{app_obj.slug}' (id={app_obj.id}, inactive)")
            except ValueError as e:
                click.echo(f"[install-app] error: {e}")
                return
            if activate:
                _activate_app_by_id(app_obj.id, _app)
            return

        # ── Fallback: Python manifest (AppHelper) ─────────────────────────────
        # Normalize: "app_soc" or "soc" → pkg "aras.app_soc"
        raw_name = app_name_or_file
        app_slug = raw_name[len("app_"):] if raw_name.startswith("app_") else raw_name
        pkg_name = f"aras.app_{app_slug}"

        try:
            import importlib
            manifest_mod = importlib.import_module(f"{pkg_name}.manifest")
            helper = getattr(manifest_mod, "helper", None)
        except ModuleNotFoundError:
            click.echo(f"[install-app] not found: no YAML file and no Python manifest at '{pkg_name}.manifest'")
            return

        from arasCore.lib.app_helper import AppHelper
        if not isinstance(helper, AppHelper):
            click.echo(f"[install-app] '{pkg_name}.manifest' has no AppHelper instance named 'helper'")
            return

        click.echo(f"[install-app] Python manifest: {pkg_name} ({len(helper.resources)} resources)")
        try:
            app_obj, stats = sync_helper_to_db(helper, db, _app)
        except Exception as e:
            click.echo(f"[install-app] sync error: {e}")
            return

        click.echo(f"[install-app] synced '{app_obj.slug}': "
                   f"{stats['tables_new']} new tables, {stats['cols_new']} new columns "
                   f"({stats['tables_existing']} tables already existed, {stats['cols_skipped']} cols skipped)")

        if activate:
            _activate_app_by_id(app_obj.id, _app)

    @aras.command("sync-app", help="Re-sync a code-based app manifest → mgr_table/mgr_column (adds new columns)")
    @click.argument("app_name")
    def sync_app(app_name):
        """
        Diff the Python manifest (AppHelper) against mgr_table/mgr_column and
        insert any new tables or columns found in the SA models.
        Existing records are never deleted.
        """
        import importlib
        import flask
        from arasCore.lib.installer import sync_helper_to_db
        from arasCore.lib.app_helper import AppHelper

        _app = flask.current_app._get_current_object()

        app_slug = app_name[len("app_"):] if app_name.startswith("app_") else app_name
        pkg_name = f"aras.app_{app_slug}"

        # Try _helper_registry first (app already loaded at startup)
        from arasCore.lib.blueprints import get_helper_registry
        registry = get_helper_registry()
        helper = registry.get(app_slug)

        if helper is None:
            try:
                mod = importlib.import_module(f"{pkg_name}.manifest")
                helper = getattr(mod, "helper", None)
            except ModuleNotFoundError:
                click.echo(f"[sync-app] no manifest found for '{pkg_name}'")
                return

        if not isinstance(helper, AppHelper):
            click.echo(f"[sync-app] '{pkg_name}.manifest' has no AppHelper instance named 'helper'")
            return

        click.echo(f"[sync-app] syncing '{helper.name}' ({len(helper.resources)} resources)...")
        try:
            _, stats = sync_helper_to_db(helper, db, _app)
        except Exception as e:
            click.echo(f"[sync-app] error: {e}")
            return

        click.echo(f"[sync-app] done: {stats['tables_new']} new tables, {stats['cols_new']} new columns "
                   f"({stats['cols_skipped']} cols already existed)")

    @aras.command("list-apps", help="List all installed (dynamic) apps")
    def list_apps():
        from arasCore.arasAdmin.models import AppManagerApp
        apps = AppManagerApp.query.order_by(AppManagerApp.menu_order, AppManagerApp.url).all()
        if not apps:
            click.echo("(no apps installed)")
            return
        click.echo(f"{'ID':<5}{'NAME':<20}{'TITLE':<25}{'URL':<20}{'ACTIVE':<8}")
        click.echo("-" * 78)
        for a in apps:
            click.echo(f"{a.id:<5}{a.name:<20}{a.title:<25}{a.url:<20}{('YES' if a.is_active else 'no'):<8}")

    @aras.command("activate-app", help="Activate an installed app (mount routes, create DB tables)")
    @click.argument("name")
    def activate_app(name):
        import flask
        from arasCore.arasAdmin.models import AppManagerApp
        row = AppManagerApp.query.filter_by(url=name).first()
        if not row:
            click.echo(f"[activate-app] '{name}' not found")
            return
        _activate_app_by_id(row.id, flask.current_app._get_current_object())

    @aras.command("deactivate-app", help="Deactivate an app (keeps data, hides from sidebar)")
    @click.argument("name")
    def deactivate_app(name):
        from arasCore.arasAdmin.models import AppManagerApp
        row = AppManagerApp.query.filter_by(url=name).first()
        if not row:
            click.echo(f"[deactivate-app] '{name}' not found")
            return
        row.is_active = False
        db.session.commit()
        click.echo(f"[deactivate-app] '{name}' deactivated. Restart server to unmount routes.")

    @aras.command("uninstall-app", help="Uninstall an app (removes metadata; optionally drops tables)")
    @click.argument("name")
    @click.option("--drop-tables", is_flag=True, default=False,
                  help="Also DROP the physical {app}_* tables")
    @click.confirmation_option(prompt="Are you sure you want to uninstall this app?")
    def uninstall_app(name, drop_tables):
        from arasCore.arasAdmin.models import AppManagerApp
        from arasCore.arasAdmin.services import clear_cache
        row = AppManagerApp.query.filter_by(url=name).first()
        if not row:
            click.echo(f"[uninstall-app] '{name}' not found")
            return
        if drop_tables:
            for tbl in row.get_tables():
                db_name = tbl.get_db_table_name(row.slug)
                try:
                    db.engine.execute(f"DROP TABLE IF EXISTS `{db_name}`")
                    click.echo(f"  dropped {db_name}")
                except Exception as e:
                    click.echo(f"  drop failed {db_name}: {e}")
        db.session.delete(row)
        db.session.commit()
        clear_cache(name)
        click.echo(f"[uninstall-app] '{name}' removed. Restart server to fully unload.")

    @aras.command("export-app", help="Export an app definition to YAML or JSON")
    @click.argument("name")
    @click.option("--format", "fmt", type=click.Choice(["yaml", "json"]), default="yaml")
    @click.option("--output", "-o", default=None, help="Output file (default: stdout)")
    def export_app(name, fmt, output):
        import yaml, json as _json
        from arasCore.arasAdmin.models import AppManagerApp
        from arasCore.arasAdmin.routes import _build_export_definition

        row = AppManagerApp.query.filter_by(url=name).first()
        if not row:
            click.echo(f"[export-app] '{name}' not found")
            return

        definition = _build_export_definition(row)
        if fmt == "yaml":
            content = yaml.dump(definition, allow_unicode=True,
                                default_flow_style=False, sort_keys=False)
        else:
            content = _json.dumps(definition, indent=2, ensure_ascii=False)

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
            click.echo(f"[export-app] wrote {output}")
        else:
            click.echo(content)

    @aras.command("new-app", help="Scaffold a minimal YAML template for a new app")
    @click.argument("name")
    @click.option("--title", default=None)
    def new_app(name, title):
        from arasCore.lib.installer import generate_yaml_template
        content = generate_yaml_template(
            app_name=name, app_title=title or name.replace("_", " ").title()
        )
        out = f"{name}.yaml"
        with open(out, "wb") as f:
            f.write(content)
        click.echo(f"[new-app] wrote {out}. Edit, then: aras install-app {out} --activate")


# ── Helpers (module-level) ────────────────────────────────────────────────────

def _resolve_install_path(name_or_file: str, flask_app) -> str:
    """Resolve an app name or file path to an absolute definition-file path."""
    import os
    if os.path.isfile(name_or_file):
        return os.path.abspath(name_or_file)

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(flask_app.root_path)))
    candidates = [
        os.path.join(os.getcwd(), f"{name_or_file}.yaml"),
        os.path.join(os.getcwd(), f"{name_or_file}.yml"),
        os.path.join(os.getcwd(), f"{name_or_file}.json"),
        os.path.join(project_root, f"{name_or_file}.yaml"),
        os.path.join(project_root, f"{name_or_file}.json"),
        os.path.join(project_root, "aras", f"app_{name_or_file}", "install.yaml"),
        os.path.join(project_root, "aras", f"app_{name_or_file}", "install.json"),
    ]
    # Also try app_install.yaml if its app.name matches
    for p in [os.path.join(os.getcwd(), "app_install.yaml"),
              os.path.join(project_root, "app_install.yaml")]:
        if os.path.isfile(p):
            try:
                import yaml
                with open(p, "r", encoding="utf-8") as f:
                    d = yaml.safe_load(f) or {}
                if (d.get("app") or {}).get("name") == name_or_file:
                    return p
            except Exception:
                pass

    for c in candidates:
        if os.path.isfile(c):
            return c
    return ""


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


def _activate_app_by_id(app_id: int, flask_app):
    """Activate + register a dynamic app. Mirrors admin UI flow."""
    from arasCore.arasAdmin.models import AppManagerApp
    from arasCore.arasAdmin.services import _register_built_app, clear_cache
    row = AppManagerApp.query.get(app_id)
    if not row:
        click.echo(f"[activate] id={app_id} not found")
        return
    row.is_active = True
    db.session.commit()
    clear_cache(row.name)
    ok = _register_built_app(app_id, flask_app)
    click.echo(
        f"[activate] '{row.name}' "
        + ("registered" if ok else "failed (see logs)")
    )
