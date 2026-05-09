import os
import sys
import click
import mariadb
from arasCore.lib.core.database import db_init, db_createall
from arasCore.lib.core.extensions import db


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


def register_db_commands(aras):
    @aras.command()
    def dbtest():
        """Test DB Connection."""
        db_conn()

    @aras.command()
    def dbinit():
        """Initialize Database metadata."""
        db_init()

    @aras.command()
    def dbca():
        """Create All Tables."""
        db_createall()

    @aras.command("migrate", help="Reconcile DB schema with current models (auto-detect drift)")
    @click.option("--force", is_flag=True, default=False,
                  help="Allow destructive ops (drop column/table, narrow type)")
    def migrate(force):
        """Model-driven migration. Diffs SQLAlchemy metadata vs live DB and applies safe changes."""
        import flask
        from arasCore.lib.services.auto_migrate import run as _auto_migrate
        if force:
            os.environ["ARAS_AUTO_DROP"] = "true"
            click.echo("[migrate] --force enabled: destructive ops will be applied")
        _app = flask.current_app._get_current_object()
        with _app.app_context():
            db.create_all()
            report = _auto_migrate(_app)
        report.log_summary()
        click.echo("[migrate] done.")

    @aras.command("fix-db", help="Alias for migrate")
    @click.option("--force", is_flag=True, default=False)
    @click.pass_context
    def fix_db(ctx, force):
        ctx.invoke(migrate, force=force)

    @aras.command("remigrate", help="db.create_all + auto_migrate + sync all manifests + ERP seed")
    @click.option("--yes", is_flag=True, default=False, help="Skip confirmation prompt")
    @click.option("--force", is_flag=True, default=False,
                  help="Allow destructive ops (drop column/table, narrow type)")
    def remigrate(yes, force):
        import flask
        _app = flask.current_app._get_current_object()

        if not yes:
            click.confirm(
                "This will run db.create_all() and reconcile schema. Continue?",
                abort=True,
            )

        if force:
            os.environ["ARAS_AUTO_DROP"] = "true"
            click.echo("[remigrate] --force enabled: destructive ops will be applied")

        # 1. Create all tables (idempotent)
        click.echo("[remigrate] 1/3  db.create_all() ...")
        with _app.app_context():
            db.create_all()

        # 2. Auto-migrate: reconcile schema to model declarations
        click.echo("[remigrate] 2/3  auto_migrate ...")
        from arasCore.lib.services.auto_migrate import run as _auto_migrate
        _auto_migrate(_app).log_summary()

        # 3. Sync all code-based manifests → mgr_table/mgr_column
        click.echo("[remigrate] 3/3  sync all manifests ...")
        from arasCore.lib.services.blueprints import get_helper_registry
        from arasCore.lib.services.installer import sync_helper_to_db
        registry = get_helper_registry()
        for slug, helper in registry.items():
            try:
                _, stats = sync_helper_to_db(helper, db, _app)
                click.echo(f"          synced '{slug}': "
                           f"+{stats['tables_new']} tables, +{stats['cols_new']} cols")
            except Exception as e:
                click.echo(f"          ERROR syncing '{slug}': {e}")

        # Emit a remigrate event so apps (e.g. ERP) can run their own seed.
        try:
            from arasCore.lib.core.events import emit
            emit("framework.remigrate", _app)
        except Exception:
            pass

        click.echo("[remigrate] all done.")
