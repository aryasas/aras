"""
Aras Framework Management CLI
Usage: python manage.py [command]
"""
import argparse
import sys
import os

# Add parent directory to path so 'api' package is discoverable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import Aras


def _discover_for_management() -> None:
    Aras.logic.discovery.discover_apps(package_path="apps")


def _sync_registry(drop_orphans: bool = False) -> None:
    print("Discovering apps...")
    _discover_for_management()

    print("Registering core master data...")
    from core.registry.master_data_entities import register_core_entities
    register_core_entities()

    print("Running auto-migration...")
    from core.logic import auto_migrate
    from core.base.model import Base
    auto_migrate.run(Aras.engine, Base.metadata, drop_orphan_tables=drop_orphans)

    print("Synchronizing metadata...")
    db = next(Aras.get_db())
    try:
        Aras.Manager.Sync.sync_all(db)
    finally:
        db.close()


def _seed_single_app(app_cls, db) -> list[str]:
    from core.manager.bootstrap import _run_app_rbac
    from core.seeds.base import run_app_seeds

    seeded: list[str] = []

    entries = getattr(app_cls, "seeds", None) or []
    if entries:
        run_app_seeds(app_cls, db)
        seeded.extend(
            getattr(entry, "label", None) or getattr(entry, "__name__", repr(entry))
            for entry in entries
        )

    _run_app_rbac(app_cls, db)

    seed = app_cls.__dict__.get("seed")
    if seed is not None:
        seed(db)
        seeded.append("legacy seed")

    return seeded


def _print_install_plan(order, include_demo: bool, org_id: int) -> None:
    print("Install plan:")
    total = len(order)
    for index, app_cls in enumerate(order, start=1):
        seed_labels = []
        for entry in getattr(app_cls, "seeds", None) or []:
            seed_labels.append(getattr(entry, "label", None) or getattr(entry, "__name__", repr(entry)))
        suffix = f" seeds=[{', '.join(seed_labels)}]" if seed_labels else " seeds=[none]"
        print(f"[{index}/{total}] {getattr(app_cls, 'app_type', 'app')}: {app_cls.app_name}{suffix}")
    if include_demo:
        print(f"[demo] demo seed for org_id={org_id}")

def main():
    parser = argparse.ArgumentParser(description="Aras Framework Manager")
    subparsers = parser.add_subparsers(dest="command")

# gemini-flash

    # Sync
    sync_parser = subparsers.add_parser("sync", help="Sync code to DB registry")
    sync_parser.add_argument("--drop-orphans", action="store_true", help="Drop orphaned tables in development mode")

    # Migrate
    migrate_parser = subparsers.add_parser("migrate", help="Run Alembic migrations")
    migrate_parser.add_argument("revision", nargs="?", default="head", help="Revision target (default: head)")

    # Install
    install_parser = subparsers.add_parser("install", help="Install app from YAML")
    install_parser.add_argument("file", help="Path to YAML file")

    install_all_parser = subparsers.add_parser("install-all", help="Install all discovered apps in dependency order")
    install_all_parser.add_argument("--demo", action="store_true", help="Run demo seed after app installs")
    install_all_parser.add_argument("--org-id", type=int, default=1, help="Organization ID for demo seed")
    install_all_parser.add_argument("--dry-run", action="store_true", help="Print the resolved plan without changing anything")

    # Discover
    discover_parser = subparsers.add_parser("discover", help="List discovered apps")

    # Uninstall
    uninstall_parser = subparsers.add_parser("uninstall", help="Remove an app from filesystem and DB")
    uninstall_parser.add_argument("name", help="Name of the app to remove")

    # Activate
    activate_parser = subparsers.add_parser("activate", help="Activate an app in the registry")
    activate_parser.add_argument("name", help="Name of the app to activate")

    # Deactivate
    deactivate_parser = subparsers.add_parser("deactivate", help="Deactivate an app in the registry")
    deactivate_parser.add_argument("name", help="Name of the app to deactivate")

    # Check
    check_parser = subparsers.add_parser("check", help="Run framework health and integrity checks")

    # Seed
    seed_parser = subparsers.add_parser("seed", help="Seed initial data for apps")
    seed_parser.add_argument("--demo", action="store_true", help="Seed with demo data")
    seed_parser.add_argument("--org-id", type=int, default=1, help="ID of the company to seed data for")

    # Tenant management
    tenant_parser = subparsers.add_parser("tenant", help="Manage tenants")
    tenant_sub = tenant_parser.add_subparsers(dest="tenant_command")
    tp = tenant_sub.add_parser("provision", help="Provision a new tenant database")
    tp.add_argument("tenant_id", help="Unique tenant identifier")
    tp.add_argument("--db-name", default=None, help="Database name (default: tenant_<tenant_id>)")
    tp.add_argument("--seed", action="store_true", help="Seed basic data after provisioning")
    tenant_sub.add_parser("list", help="List all registered tenants")
    td = tenant_sub.add_parser("deprovision", help="Soft-delete a tenant database")
    td.add_argument("tenant_id", help="Tenant ID to deprovision")
    ts = tenant_sub.add_parser("seed", help="Seed basic data into a tenant database")
    ts.add_argument("tenant_id", help="Tenant ID to seed")

    # Cleanup
    subparsers.add_parser("cleanup", help="Delete inactive (stale) app/resource/field rows from registry")

    # Fetch Geo
    subparsers.add_parser("fetch-geo", help="Download GeoLite2-Country database")

    args = parser.parse_args()


    if args.command == "sync":
        _sync_registry(drop_orphans=args.drop_orphans)
        print("Done.")

    elif args.command == "migrate":
        from alembic import command
        from alembic.config import Config
        cfg = Config(os.path.join(os.path.dirname(__file__), "alembic.ini"))
        command.upgrade(cfg, args.revision)
    
    elif args.command == "install":
        if not os.path.exists(args.file):
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
            
        try:
            installer = Aras.logic.installer.AppInstaller
            if args.file.endswith((".yaml", ".yml")):
                with open(args.file, "r") as f:
                    content = f.read()
                path = installer.install_from_yaml(content)
            elif args.file.endswith(".json"):
                with open(args.file, "r") as f:
                    content = f.read()
                path = installer.install_from_json(content)
            elif args.file.endswith(".zip"):
                with open(args.file, "rb") as f:
                    content = f.read()
                path = installer.install_from_zip(content)
            else:
                print("Error: Unsupported file format. Use .yaml, .json, or .zip")
                sys.exit(1)

            print(f"App installed successfully at {path}")
            print("Run 'python manage.py sync' to update the registry.")
        except Exception as e:
            print(f"Installation failed: {str(e)}")
            sys.exit(1)

    elif args.command == "uninstall":
        try:
            db = next(Aras.get_db())
            installer = Aras.logic.installer.AppInstaller
            if installer.uninstall_app(args.name, db=db):
                print(f"App '{args.name}' uninstalled and cleaned from database.")
            else:
                # Still try to purge from DB even if files are missing
                installer.purge_app_from_db(args.name, db)
                print(f"App '{args.name}' purged from database (files were already missing).")
        except Exception as e:
            print(f"Uninstallation failed: {str(e)}")
            sys.exit(1)

    elif args.command == "activate":
        from core.registry.app_model import AppModel
        db = next(Aras.get_db())
        app = db.query(AppModel).filter(AppModel.name == args.name).first()
        if app:
            app.is_active = True
            db.commit()
            print(f"App '{args.name}' activated.")
        else:
            print(f"Error: App '{args.name}' not found in registry.")

    elif args.command == "deactivate":
        from core.registry.app_model import AppModel
        db = next(Aras.get_db())
        app = db.query(AppModel).filter(AppModel.name == args.name).first()
        if app:
            app.is_active = False
            db.commit()
            print(f"App '{args.name}' deactivated.")
        else:
            print(f"Error: App '{args.name}' not found in registry.")

    elif args.command == "discover":
        _discover_for_management()
        registered_apps = Aras.App._registry
        if not registered_apps:
            print("No apps discovered.")
        else:
            print(f"Discovered {len(registered_apps)} apps:")
            for name, cls in registered_apps.items():
                print(f"- {name} ({cls.app_label}) v{getattr(cls, 'version', '1.0.0')}")

    elif args.command == "install-all":
        from core.manager.install_order import resolve_install_order
        from core.registry.app_model import AppModel

        _discover_for_management()
        order = resolve_install_order()

        if args.dry_run:
            _print_install_plan(order, include_demo=args.demo, org_id=args.org_id)
            return

        _sync_registry()
        db = next(Aras.get_db())
        try:
            app_rows = {
                row.name: row
                for row in db.query(AppModel).filter(AppModel.name.in_([app.app_name for app in order])).all()
            }
            total = len(order)
            for index, app_cls in enumerate(order, start=1):
                app_row = app_rows.get(app_cls.app_name)
                if app_row:
                    app_row.is_active = True
                    db.flush()
                seeded = _seed_single_app(app_cls, db)
                db.commit()
                summary = ", ".join(seeded) if seeded else "none"
                print(f"[{index}/{total}] {getattr(app_cls, 'app_type', 'app')}: {app_cls.app_name} ... seeded ({summary})")

            if args.demo:
                from seeds.demo import run_seed as seed_demo_data

                seed_demo_data(db, args.org_id)
                db.commit()
                print(f"[demo] demo data seeded for org_id={args.org_id}")
        except Exception as e:
            db.rollback()
            print(f"Install-all failed: {e}")
            sys.exit(1)
        finally:
            db.close()

    elif args.command == "check":
        print("Running Health Checks...")
        from core.manager.health_manager import HealthManager
        db = next(Aras.get_db())
        report = HealthManager.run_all_checks(db)
        
        has_issues = False
        for category, issues in report.items():
            if issues:
                has_issues = True
                print(f"\n[!] {category.replace('_', ' ').title()}:")
                for issue in issues:
                    print(f"  - {issue}")
        
        if not has_issues:
            print("\n[✓] All checks passed. System is healthy.")
        else:
            print("\n[!] Health checks found issues that may need attention.")

    elif args.command == "seed":
        # Imports here, specifically for the seed command
        from core.lib.database import SessionLocal
        from seeds.demo import run_seed as seed_demo_data
        from core.workspace.models import Organization

        print("Discovering apps...")
        _discover_for_management()

        print(f"Seeding initial data for org ID: {args.org_id}...")
        db = SessionLocal()
        try:
            company = Organization.find(db, id=args.org_id)
            if not company:
                print(f"Error: Organization with ID {args.org_id} not found.")
                sys.exit(1)
            
            # Run core ERP seeding via standardized App.seed() method
            registered_apps = Aras.App._registry
            for name, app_cls in registered_apps.items():
                print(f"  - Seeding app: {name}...")
                app_cls.seed(db)
            
            if args.demo:
                print("  - Seeding Demo Data...")
                seed_demo_data(db, company.id)
            
            db.commit()
            print("Seeding completed successfully.")
        except Exception as e:
            db.rollback()
            print(f"Seeding failed: {str(e)}")
            import traceback
            traceback.print_exc() # Print full traceback for debugging
            sys.exit(1)
        finally:
            db.close()

    elif args.command == "tenant":
        from core.tenant.provisioner import provision_tenant, deprovision_tenant, seed_tenant
        from core.tenant.registry import tenant_registry

        if args.tenant_command == "list":
            tenants = tenant_registry.list_all()
            if not tenants:
                print("No tenants registered.")
            else:
                for t in tenants:
                    print(f"  {t['tenant_id']}  →  {t.get('meta', {}).get('db_name', 'unknown')}")

        elif args.tenant_command == "provision":
            db_name = args.db_name or f"tenant_{args.tenant_id}"
            print(f"Provisioning tenant '{args.tenant_id}' (db: {db_name})...")
            try:
                info = provision_tenant(args.tenant_id, db_name)
                print(f"  Provisioned: {info}")
                if args.seed:
                    print(f"  Seeding tenant '{args.tenant_id}'...")
                    result = seed_tenant(args.tenant_id)
                    print(f"  Seeded: {result['seeded']}")
            except Exception as e:
                print(f"Error: {e}")
                sys.exit(1)

        elif args.tenant_command == "seed":
            print(f"Seeding tenant '{args.tenant_id}'...")
            try:
                result = seed_tenant(args.tenant_id)
                print(f"  Seeded: {result['seeded']}")
            except Exception as e:
                print(f"Error: {e}")
                sys.exit(1)

        elif args.tenant_command == "deprovision":
            print(f"Deprovisioning tenant '{args.tenant_id}'...")
            ok = deprovision_tenant(args.tenant_id)
            if ok:
                print(f"  Tenant '{args.tenant_id}' deprovisioned.")
            else:
                print(f"  Tenant '{args.tenant_id}' not found.")
                sys.exit(1)
        else:
            tenant_parser.print_help()

    elif args.command == "cleanup":
        from core.lib.database import SessionLocal
        from core.registry.app_model import AppModel
        from core.registry.resource_model import ResourceModel
        from core.registry.field_model import FieldModel
        db = SessionLocal()
        try:
            stale_apps = db.query(AppModel).filter(AppModel.is_active == False).all()
            if not stale_apps:
                print("Nothing to clean up.")
            else:
                print(f"Found {len(stale_apps)} inactive app(s):")
                for a in stale_apps:
                    print(f"  - {a.name}")
                    from core.registry.link_model import LinkModel
                    resources = db.query(ResourceModel).filter(ResourceModel.app_id == a.id).all()
                    resource_ids = [r.id for r in resources]
                    db.query(LinkModel).filter(
                        LinkModel.source_resource_id.in_(resource_ids) |
                        LinkModel.target_resource_id.in_(resource_ids)
                    ).delete(synchronize_session=False)
                    db.query(FieldModel).filter(FieldModel.resource_id.in_(resource_ids)).delete(synchronize_session=False)
                    for r in resources:
                        db.delete(r)
                    db.flush()
                    db.delete(a)
                db.commit()
                print("Cleanup complete.")
        except Exception as e:
            db.rollback()
            print(f"Error: {e}")
            sys.exit(1)
        finally:
            db.close()

    elif args.command == "fetch-geo":
        try:
            from api.scripts.fetch_geolite import fetch_geolite
        except ImportError:
            try:
                from scripts.fetch_geolite import fetch_geolite
            except ImportError:
                print("Error: Could not import fetch_geolite. Ensure api/scripts/fetch_geolite.py exists.")
                sys.exit(1)
        fetch_geolite()

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
