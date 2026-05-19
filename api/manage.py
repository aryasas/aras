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

def main():
    parser = argparse.ArgumentParser(description="Aras Framework Manager")
    subparsers = parser.add_subparsers(dest="command")

    # Sync
    sync_parser = subparsers.add_parser("sync", help="Sync code to DB registry")

    # Install
    install_parser = subparsers.add_parser("install", help="Install app from YAML")
    install_parser.add_argument("file", help="Path to YAML file")

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
    tp.add_argument("--db-name", default=None, help="Database name (default: aras_tenant_<tenant_id>)")
    tp.add_argument("--seed", action="store_true", help="Seed basic data after provisioning")
    tenant_sub.add_parser("list", help="List all registered tenants")
    td = tenant_sub.add_parser("deprovision", help="Soft-delete a tenant database")
    td.add_argument("tenant_id", help="Tenant ID to deprovision")
    ts = tenant_sub.add_parser("seed", help="Seed basic data into a tenant database")
    ts.add_argument("tenant_id", help="Tenant ID to seed")

    # Cleanup
    subparsers.add_parser("cleanup", help="Delete inactive (stale) app/resource/field rows from registry")

    args = parser.parse_args()


    if args.command == "sync":
        print("Discovering apps...")
        Aras.logic.discovery.discover_apps(package_path="apps")

        print("Creating tables...")
        Aras.Base.metadata.create_all(bind=Aras.engine)

        # Pre-migrate so sync_all's queries see any new columns (e.g. scoped_by).
        print("Auto-migrating schema...")
        from core.logic import auto_migrate
        report = auto_migrate.run(Aras.engine, Aras.Base.metadata)
        if report.errors:
            print(f"Auto-migration errors: {report.errors}")

        print("Synchronizing metadata...")
        db = next(Aras.get_db())
        Aras.Manager.Sync.sync_all(db)
        print("Done.")
    
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
        Aras.logic.discovery.discover_apps(package_path="apps")
        registered_apps = Aras.App._registry
        if not registered_apps:
            print("No apps discovered.")
        else:
            print(f"Discovered {len(registered_apps)} apps:")
            for name, cls in registered_apps.items():
                print(f"- {name} ({cls.app_label}) v{getattr(cls, 'version', '1.0.0')}")

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
        from apps.erp.config.seed_rbac import run_seed as seed_rbac
        from apps.erp.accounting.seed_coa import seed_coa
        from apps.erp.report.seed_reports import run_seed as seed_reports
        from apps.erp.seed_demo import run_seed as seed_demo_data
        from apps.erp.config.models import Organization

        print("Discovering apps...")
        Aras.logic.discovery.discover_apps(package_path="apps")

        print(f"Seeding initial data for org ID: {args.org_id}...")
        db = SessionLocal()
        try:
            company = Organization.find(db, id=args.org_id)
            if not company:
                print(f"Error: Organization with ID {args.org_id} not found.")
                sys.exit(1)
            
            # Run core ERP seeding
            print("  - Seeding Chart of Accounts...")
            seed_rbac(db)
            seed_coa(db, company.id)
            print("  - Seeding Reports...")
            seed_reports(db, company.id)
            
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
            db_name = args.db_name or f"aras_tenant_{args.tenant_id}"
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

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
