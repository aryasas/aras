import os
import click
from arasCore.lib.core.extensions import db

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
        os.path.join(project_root, "app", f"app_{name_or_file}", "install.yaml"),
        os.path.join(project_root, "app", f"app_{name_or_file}", "install.json"),
    ]
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

def _activate_app_by_id(app_id: int, flask_app):
    """Activate + register a dynamic app. Mirrors admin UI flow."""
    from arasCore.admin.models import AppManagerApp
    from arasCore.admin.services import _register_built_app, clear_cache
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

def register_app_commands(aras):
    @aras.command("install-app", help="Install an app from YAML/JSON or Python manifest")
    @click.argument("app_name_or_file")
    @click.option("--activate", is_flag=True, default=False,
                  help="Activate immediately after install (creates DB tables)")
    def install_app(app_name_or_file, activate):
        import yaml, json as _json
        import flask
        from arasCore.lib.services.installer import install_from_definition, parse_app_definition, sync_helper_to_db

        _app = flask.current_app._get_current_object()
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

        raw_name = app_name_or_file
        app_slug = raw_name[len("app_"):] if raw_name.startswith("app_") else raw_name
        pkg_name = f"app.{app_slug}"

        try:
            import importlib
            manifest_mod = importlib.import_module(f"{pkg_name}.manifest")
            helper = getattr(manifest_mod, "helper", None)
        except ModuleNotFoundError:
            click.echo(f"[install-app] not found: no YAML file and no Python manifest at '{pkg_name}.manifest'")
            return

        from arasCore.lib.services.app_helper import AppHelper
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
                   f"{stats['tables_new']} new tables, {stats['cols_new']} new columns")

        if activate:
            _activate_app_by_id(app_obj.id, _app)

    @aras.command("sync-app", help="Re-sync a code-based app manifest → mgr_table/mgr_column")
    @click.argument("app_name")
    def sync_app(app_name):
        import importlib
        import flask
        from arasCore.lib.services.installer import sync_helper_to_db
        from arasCore.lib.services.app_helper import AppHelper

        _app = flask.current_app._get_current_object()
        app_slug = app_name[len("app_"):] if app_name.startswith("app_") else app_name
        pkg_name = f"app.{app_slug}"

        from arasCore.lib.services.blueprints import get_helper_registry
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

        click.echo(f"[sync-app] syncing '{helper.name}'...")
        try:
            _, stats = sync_helper_to_db(helper, db, _app)
            click.echo(f"[sync-app] done: {stats['tables_new']} new tables, {stats['cols_new']} new columns")
        except Exception as e:
            click.echo(f"[sync-app] error: {e}")

    @aras.command("list-apps", help="List all installed (dynamic) apps")
    def list_apps():
        from arasCore.admin.models import AppManagerApp
        apps = AppManagerApp.query.order_by(AppManagerApp.menu_order, AppManagerApp.url).all()
        if not apps:
            click.echo("(no apps installed)")
            return
        click.echo(f"{'ID':<5}{'NAME':<20}{'TITLE':<25}{'URL':<20}{'ACTIVE':<8}")
        click.echo("-" * 78)
        for a in apps:
            click.echo(f"{a.id:<5}{a.name:<20}{a.title:<25}{a.url:<20}{('YES' if a.is_active else 'no'):<8}")

    @aras.command("activate-app", help="Activate an installed app")
    @click.argument("name")
    def activate_app(name):
        import flask
        from arasCore.admin.models import AppManagerApp
        row = AppManagerApp.query.filter_by(url=name).first()
        if not row:
            click.echo(f"[activate-app] '{name}' not found")
            return
        _activate_app_by_id(row.id, flask.current_app._get_current_object())

    @aras.command("deactivate-app", help="Deactivate an app")
    @click.argument("name")
    def deactivate_app(name):
        from arasCore.admin.models import AppManagerApp
        row = AppManagerApp.query.filter_by(url=name).first()
        if not row:
            click.echo(f"[deactivate-app] '{name}' not found")
            return
        row.is_active = False
        db.session.commit()
        click.echo(f"[deactivate-app] '{name}' deactivated.")

    @aras.command("uninstall-app", help="Uninstall an app")
    @click.argument("name")
    @click.option("--drop-tables", is_flag=True, default=False)
    @click.confirmation_option(prompt="Are you sure?")
    def uninstall_app(name, drop_tables):
        from arasCore.admin.models import AppManagerApp
        from arasCore.admin.services import clear_cache
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
        click.echo(f"[uninstall-app] '{name}' removed.")

    @aras.command("export-app", help="Export an app definition")
    @click.argument("name")
    @click.option("--format", "fmt", type=click.Choice(["yaml", "json"]), default="yaml")
    @click.option("--output", "-o", default=None)
    def export_app(name, fmt, output):
        import yaml, json as _json
        from arasCore.admin.models import AppManagerApp
        from arasCore.admin.routes import _build_export_definition

        row = AppManagerApp.query.filter_by(url=name).first()
        if not row:
            click.echo(f"[export-app] '{name}' not found")
            return

        definition = _build_export_definition(row)
        if fmt == "yaml":
            content = yaml.dump(definition, allow_unicode=True, default_flow_style=False, sort_keys=False)
        else:
            content = _json.dumps(definition, indent=2, ensure_ascii=False)

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
            click.echo(f"[export-app] wrote {output}")
        else:
            click.echo(content)

    @aras.command("new-app", help="Scaffold a minimal YAML template")
    @click.argument("name")
    @click.option("--title", default=None)
    def new_app(name, title):
        from arasCore.lib.services.installer import generate_yaml_template
        content = generate_yaml_template(app_name=name, app_title=title or name.replace("_", " ").title())
        out = f"{name}.yaml"
        with open(out, "wb") as f:
            f.write(content)
        click.echo(f"[new-app] wrote {out}.")
