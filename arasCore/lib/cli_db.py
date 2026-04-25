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
        except (ModuleNotFoundError, ImportError):
            # Fallback for dynamic imports or if module doesn't exist
            click.echo("          app_erp not fully installed or seed modules missing — skipped.")

        click.echo("[remigrate] all done.")

    @aras.command("fix-db", help="Auto-discover all models and add missing columns to live DB")
    @click.option("--dry-run", is_flag=True, help="Print what would change without applying")
    def fix_db(dry_run):
        import flask
        from sqlalchemy import inspect as sa_inspect

        _app = flask.current_app._get_current_object()
        with _app.app_context():
            inspector = sa_inspect(db.engine)
            existing_tables = set(inspector.get_table_names())

            seen: dict = {}
            for mapper in db.Model.registry.mappers:
                cls = mapper.class_
                tbl = getattr(cls, "__tablename__", None)
                if tbl and tbl not in seen:
                    seen[tbl] = cls
            models = seen.values()

            added = dropped = errors = 0
            with db.engine.connect() as conn:
                for model in sorted(models, key=lambda m: m.__tablename__):
                    tbl_name = model.__tablename__
                    if tbl_name not in existing_tables:
                        click.echo(f"  MISSING TABLE  {tbl_name}")
                        continue

                    live_cols = {c["name"] for c in inspector.get_columns(tbl_name)}
                    sa_table = model.__table__

                    for col in sa_table.columns:
                        if col.name in live_cols:
                            continue
                        try:
                            col_ddl = col.type.compile(dialect=db.engine.dialect)
                        except Exception:
                            col_ddl = str(col.type)

                        parts = [f"`{col.name}`", col_ddl]
                        if not col.nullable: parts.append("NOT NULL")
                        
                        if col.server_default is not None:
                            clause = getattr(col.server_default, "arg", None)
                            if clause is not None: parts.append(f"DEFAULT {clause}")
                        elif col.default is not None and hasattr(col.default, "arg"):
                            arg = col.default.arg
                            if not callable(arg): parts.append(f"DEFAULT {arg!r}")
                        elif col.nullable:
                            parts.append("DEFAULT NULL")

                        ddl = f"ALTER TABLE `{tbl_name}` ADD COLUMN {' '.join(parts)}"
                        if dry_run:
                            click.echo(f"  WOULD ADD  {tbl_name}.{col.name}")
                            added += 1
                        else:
                            try:
                                conn.execute(db.text(ddl))
                                click.echo(f"  ADDED      {tbl_name}.{col.name}")
                                added += 1
                            except Exception as e:
                                click.echo(f"  ERROR      {tbl_name}.{col.name}: {e}")
                                errors += 1

                    if "created_by" in live_cols and "created_by_id" in live_cols:
                        if dry_run:
                            dropped += 1
                        else:
                            try:
                                conn.execute(db.text(f"ALTER TABLE `{tbl_name}` DROP COLUMN `created_by`"))
                                dropped += 1
                            except Exception:
                                errors += 1
                if not dry_run: conn.commit()

        tag = "[fix-db dry-run]" if dry_run else "[fix-db]"
        click.echo(f"{tag} added={added} dropped={dropped} errors={errors}")
