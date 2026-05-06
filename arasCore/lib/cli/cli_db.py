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

    @aras.command("migrate", help="Run arasCore idempotent migrations (page type, settings, etc.)")
    def migrate():
        import flask
        import importlib as _ilib
        from arasCore.lib.migrations import m001_page_type, m002_rbac, m004_arasmodel_audit_cols, m005_list_view_setting
        _app = flask.current_app._get_current_object()
        m001_page_type.run(_app)
        m002_rbac.run(_app)
        m004_arasmodel_audit_cols.run(_app)
        m005_list_view_setting.run(_app)
        # ERP-specific migrations (idempotent — safe to run on every migrate)
        for _mname in (
            "app.erp.migrations.021_restructure_charge_mop_shift",
            "app.erp.migrations.022_invoice_payment_coa_group",
            "app.erp.migrations.023_supplier_module",
            "app.erp.migrations.024_invoice_supplier_warehouse",
            "app.erp.migrations.025_warehouse_group_product_warehouse",
        ):
            try:
                _ilib.import_module(_mname).run(_app)
            except (ModuleNotFoundError, ImportError) as _e:
                click.echo(f"          [migrate] skipped {_mname}: {_e}")
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

        # 4. ERP migrations + seed (if erp is present)
        click.echo("[remigrate] 4/4  ERP migrations + seed (if installed) ...")
        try:
            from app.erp.erp_core.migrate_task4 import run as mt4
            from app.erp.erp_core.migrate_task5 import run as mt5
            from app.erp.erp_core.migrate_task6 import run as mt6
            import importlib as _ilib
            m021 = _ilib.import_module("app.erp.migrations.021_restructure_charge_mop_shift")
            m022 = _ilib.import_module("app.erp.migrations.022_invoice_payment_coa_group")
            from app.erp.erp_core.seed import run_seed
            mt4(_app)
            mt5(_app)
            mt6(_app)
            m021.run(_app)
            m022.run(_app)
            run_seed(_app)
            click.echo("          ERP done.")
        except (ModuleNotFoundError, ImportError):
            # Fallback for dynamic imports or if module doesn't exist
            click.echo("          erp not fully installed or seed modules missing — skipped.")

        click.echo("[remigrate] all done.")

    @aras.command("fix-db", help="Auto-discover all models and fix mismatches (missing columns, type drifts)")
    @click.option("--dry-run", is_flag=True, help="Print what would change without applying")
    @click.option("--verbose", is_flag=True, help="Show more detail about checks")
    def fix_db(dry_run, verbose):
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

            added = altered = dropped = errors = 0
            with db.engine.connect() as conn:
                for model in sorted(models, key=lambda m: m.__tablename__):
                    tbl_name = model.__tablename__
                    if tbl_name not in existing_tables:
                        if verbose: click.echo(f"  SKIP       {tbl_name} (table not in DB)")
                        continue

                    live_cols_raw = inspector.get_columns(tbl_name)
                    live_cols = {c["name"]: c for c in live_cols_raw}
                    live_indexes = inspector.get_indexes(tbl_name)
                    live_idx_cols = set()
                    for idx in live_indexes:
                        for cname in idx["column_names"]: live_idx_cols.add(cname)

                    sa_table = model.__table__

                    for col in sa_table.columns:
                        if col.name not in live_cols:
                            # 1. MISSING COLUMN
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
                                    click.echo(f"  ERROR ADD  {tbl_name}.{col.name}: {e}")
                                    errors += 1
                        else:
                            # 2. TYPE MISMATCH check (Simplified)
                            live_col = live_cols[col.name]
                            live_type_str = str(live_col["type"]).upper()
                            try:
                                target_type_str = col.type.compile(dialect=db.engine.dialect).upper()
                            except Exception:
                                target_type_str = str(col.type).upper()

                            # Normalize common aliases (MARIADB/MYSQL)
                            norm_live = live_type_str.replace("TINYINT(1)", "BOOLEAN").replace("INTEGER", "INT")
                            norm_target = target_type_str.replace("TINYINT(1)", "BOOLEAN").replace("INTEGER", "INT")
                            
                            # Stripping lengths for a basic check if they match mostly
                            if norm_live != norm_target and not (norm_live.startswith(norm_target) or norm_target.startswith(norm_live)):
                                if verbose: click.echo(f"  DRIFT      {tbl_name}.{col.name}: {live_type_str} -> {target_type_str}")
                                # Generating MODIFY column
                                ddl = f"ALTER TABLE `{tbl_name}` MODIFY COLUMN `{col.name}` {target_type_str}"
                                if not col.nullable: ddl += " NOT NULL"
                                
                                if dry_run:
                                    click.echo(f"  WOULD MOD  {tbl_name}.{col.name} type")
                                    altered += 1
                                else:
                                    try:
                                        conn.execute(db.text(ddl))
                                        click.echo(f"  MODIFIED   {tbl_name}.{col.name} type")
                                        altered += 1
                                    except Exception as e:
                                        click.echo(f"  ERROR MOD  {tbl_name}.{col.name}: {e}")
                                        errors += 1
                            
                            # 3. INDEX MISMATCH check
                            if col.index and col.name not in live_idx_cols:
                                idx_name = f"ix_{tbl_name}_{col.name}"
                                ddl = f"CREATE INDEX `{idx_name}` ON `{tbl_name}` (`{col.name}`)"
                                if dry_run:
                                    click.echo(f"  WOULD IDX  {tbl_name}.{col.name}")
                                    altered += 1
                                else:
                                    try:
                                        conn.execute(db.text(ddl))
                                        click.echo(f"  INDEXED    {tbl_name}.{col.name}")
                                        altered += 1
                                    except Exception as e:
                                        click.echo(f"  ERROR IDX  {tbl_name}.{col.name}: {e}")
                                        errors += 1

                    # 4. HACK: Cleanup legacy columns
                    if "created_by" in live_cols and "created_by_id" in live_cols:
                        if dry_run:
                            click.echo(f"  WOULD DROP {tbl_name}.created_by (legacy)")
                            dropped += 1
                        else:
                            try:
                                conn.execute(db.text(f"ALTER TABLE `{tbl_name}` DROP COLUMN `created_by`"))
                                click.echo(f"  DROPPED    {tbl_name}.created_by")
                                dropped += 1
                            except Exception:
                                errors += 1
                if not dry_run: conn.commit()

        tag = "[fix-db dry-run]" if dry_run else "[fix-db]"
        click.echo(f"{tag} added={added} altered={altered} dropped={dropped} errors={errors}")
