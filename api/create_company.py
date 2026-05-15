import sys
import os

# Add 'api' directory to path so 'core' is discoverable as a top-level package
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from core.lib.database import SessionLocal
from core import Aras # Needed for registry access
from core.logic import discovery

def create_initial_company():
    # Ensure apps are discovered and models are registered
    print("Discovering apps and registering models...")
    discovery.discover_apps(package_path="apps")

    db = SessionLocal()
    try:
        CompanyClass = Aras.Model._registry["Company"] # Get Company model from registry
        
        # Check if a company with ID 1 already exists
        existing_company = CompanyClass.find(db, id=1)
        if existing_company:
            print(f"Company with ID 1 ('{existing_company.name}') already exists. Skipping creation.")
            return existing_company

        # Create a new company
        print("Creating initial company 'HQ' with ID 1...")
        company, created = CompanyClass.get_or_create(
            db,
            defaults={"name": "Headquarters"},
            id=1, code="HQ" # Explicitly setting ID to 1 for consistency
        )
        db.commit()
        if created:
            print(f"Company '{company.name}' (ID: {company.id}, Code: {company.code}) created successfully.")
        else:
            print(f"Company '{company.name}' (ID: {company.id}, Code: {company.code}) already exists.")
        return company
    except Exception as e:
        db.rollback()
        print(f"Error creating company: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    create_initial_company()