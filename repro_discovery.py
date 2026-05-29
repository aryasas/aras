import os
import sys
import importlib
import pkgutil

# Mimic manage.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'api')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

print("sys.path:")
for p in sys.path:
    print(f"  {p}")

import apps
print(f"apps.__path__: {apps.__path__}")

def discover_debug(package_path="apps"):
    package = importlib.import_module(package_path)
    for loader, module_name, is_pkg in pkgutil.walk_packages(package.__path__, package_path + "."):
        print(f"Found module: {module_name}")
        try:
            importlib.import_module(module_name)
        except Exception as e:
            print(f"  Error importing {module_name}: {e}")

discover_debug()

print("\nTriggering SQLAlchemy configuration...")
from core.lib.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
try:
    # Triggering configuration by querying any model or even just text if it triggers mappers
    from core.registry.resource_model import ResourceModel
    db.query(ResourceModel).first()
    print("Success!")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
