"""
Aras Framework Management CLI
Usage: python manage.py [command]
"""
import argparse
import sys
import os

# Add current directory to path so core and apps can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core import Aras
from core.lib.discovery import discover_apps
from core.lib.installer import AppInstaller

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

    args = parser.parse_args()

    if args.command == "sync":
        print("Discovering apps...")
        discover_apps(package_path="apps")

        print("Creating tables...")
        from core import Aras
        Aras.Base.metadata.create_all(bind=Aras.engine)

        print("Synchronizing metadata...")
        db = next(Aras.get_db())
        Aras.Manager.Sync.sync_all(db)
        print("Done.")
    
    elif args.command == "install":
        if not os.path.exists(args.file):
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
            
        try:
            if args.file.endswith((".yaml", ".yml")):
                with open(args.file, "r") as f:
                    content = f.read()
                path = AppInstaller.install_from_yaml(content)
            elif args.file.endswith(".json"):
                with open(args.file, "r") as f:
                    content = f.read()
                path = AppInstaller.install_from_json(content)
            elif args.file.endswith(".zip"):
                with open(args.file, "rb") as f:
                    content = f.read()
                path = AppInstaller.install_from_zip(content)
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
            if AppInstaller.uninstall_app(args.name, db=db):
                print(f"App '{args.name}' uninstalled and cleaned from database.")
            else:
                # Still try to purge from DB even if files are missing
                AppInstaller.purge_app_from_db(args.name, db)
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
        discover_apps(package_path="apps")
        registered_apps = Aras.App._registry
        if not registered_apps:
            print("No apps discovered.")
        else:
            print(f"Discovered {len(registered_apps)} apps:")
            for name, cls in registered_apps.items():
                print(f"- {name} ({cls.app_label}) v{getattr(cls, 'version', '1.0.0')}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
