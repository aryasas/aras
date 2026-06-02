import sys
import os
from sqlalchemy import text

# Add 'api' directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "api")))

from core.lib.database import SessionLocal
from core.logic import discovery

def check_reports():
    discovery.discover_apps(package_path="api/apps")
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT id, code, name, org_id FROM erp_report_reports")).fetchall()
        print(f"Total reports: {len(result)}")
        for row in result:
            print(f"ID: {row[0]}, Code: {row[1]}, Name: {row[2]}, OrgID: {row[3]}")
            
        orgs = db.execute(text("SELECT id, name FROM erp_config_organizations")).fetchall()
        print("
Organizations:")
        for row in orgs:
            print(f"ID: {row[0]}, Name: {row[1]}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_reports()
