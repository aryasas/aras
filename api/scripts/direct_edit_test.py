# gemini-pro
import sys
import os

# Add api to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core import Aras
from core.lib.database import SessionLocal
from apps.saas.models import Plan
from apps.web.models import LandingSection
import logging

logging.basicConfig(level=logging.INFO)

def test_direct_edits():
    db = SessionLocal()
    Aras.logic.discovery.discover_apps(package_path="apps")
    
    print("\n=== 1. Testing Direct SaaS Plan Edit ===")
    lite_plan = db.query(Plan).filter_by(plan_key="lite").first()
    if lite_plan:
        old_price = lite_plan.price
        new_price = 75000
        print(f"Plan found: {lite_plan.name}. Current Price: {old_price}")
        
        # Simulating an update from the Admin UI
        lite_plan.price = new_price
        db.commit()
        db.refresh(lite_plan)
        
        print(f"Update Success! New Price: {lite_plan.price}")
        
        # Revert for cleanliness
        lite_plan.price = old_price
        db.commit()
    else:
        print("Plan 'lite' not found. Run bootstrap first.")

    print("\n=== 2. Testing Landing Section Reorder (DnD Backend) ===")
    # Ensure at least 2 sections exist
    s1, _ = LandingSection.get_or_create(db, {"title": "Hero", "body": "Welcome", "sort_order": 1}, key="hero")
    s2, _ = LandingSection.get_or_create(db, {"title": "Features", "body": "Check this", "sort_order": 2}, key="features")
    db.commit()
    
    print(f"Initial State: {s1.key}({s1.sort_order}), {s2.key}({s2.sort_order})")
    
    # Simulate DnD swap: moving features to top
    print("Simulating DnD reorder action...")
    s2.reorder(db, sort_order=0) 
    # (Note: reorder method in model.py calls commit)
    
    db.refresh(s1)
    db.refresh(s2)
    print(f"Final State: {s1.key}({s1.sort_order}), {s2.key}({s2.sort_order})")
    
    if s2.sort_order == 0:
        print("SUCCESS: DnD reorder action verified on backend.")
    else:
        print("FAILED: Reorder action did not persist.")

    db.close()

if __name__ == "__main__":
    test_direct_edits()
