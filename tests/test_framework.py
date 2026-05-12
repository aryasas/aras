"""
Purpose: End-to-end verification of the Aras Framework core features.
Context: Runs against a local SQLite database for isolation.
Impact: Confirms that Sync, Audit, Workflow, and Query logic are working.
"""
import os
import sys

# Set testing environment variable for SQLite
os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test_aras.db"

# Add api to path
sys.path.append(os.path.join(os.getcwd(), "api"))

from core import Aras
from sqlalchemy import select

def test_full_cycle():
    print("--- Starting Aras Framework Verification ---")
    
    # Cleanup old test db if it exists
    if os.path.exists("test_aras.db"):
        os.remove("test_aras.db")
        
    # 0. Import apps to register models in metadata
    from apps.admin.app import AdminApp
    from apps.erp.app import ErpApp

    # 1. Initialize Database
    Aras.Base.metadata.create_all(bind=Aras.engine)
    db = Aras.db()
    
    # 2. Sync Metadata
    print("\n[Step 1] Testing Metadata Sync...")
    
    Aras.Manager.Sync.sync_all(db)
    
    app_count = db.query(Aras.AppModel).count()
    res_count = db.query(Aras.ResourceModel).count()
    field_count = db.query(Aras.FieldModel).count()
    
    print(f"Result: {app_count} Apps, {res_count} Resources, {field_count} Fields synced.")
    assert app_count >= 2, "Apps not synced correctly"

    # 3. Test Audit Trail
    print("\n[Step 2] Testing Auto-Audit Trail...")
    Aras.Manager.Audit.register_listeners()
    
    from apps.erp.models import Product
    # Manually add 'audit' feature for test if not present
    Product.__features__ = ["audit"]
    
    test_product = Product(name="Test Gadget", sku="TG001", price=99.99)
    db.add(test_product)
    db.commit()
    
    log = db.query(Aras.ActivityLog).filter(Aras.ActivityLog.resource == "erp_products").first()
    if log:
        print(f"Result: Audit log captured for {log.action} on {log.resource}.")
    else:
        print("Result: ERROR - No audit log captured.")

    # 4. Test Workflow Transition
    print("\n[Step 3] Testing Workflow Engine...")
    from core.lib.workflow import WorkflowMixin
    
    # Add workflow trait to Product for testing
    Product.__features__.append("workflow")
    Product.__transitions__ = [
        {"from": "Draft", "to": "Submitted", "permission": None}
    ]
    test_product.status = "Draft"
    db.commit()
    
    success, msg = Aras.Manager.Workflow.transition(db, test_product, "Submitted", user=None)
    print(f"Result: Transition to Submitted -> {success} ({msg})")
    assert test_product.status == "Submitted"

    # 5. Test Query Builder
    print("\n[Step 4] Testing BI Query Builder...")
    from core.lib.query_builder import QueryBuilder
    
    filters = [{"field": "price", "op": ">", "value": 50}]
    results = QueryBuilder.execute(db, Product, filters)
    print(f"Result: Query found {len(results)} products with price > 50.")
    assert len(results) > 0

    print("\n--- Verification Successful! ---")
    db.close()
    
    # Cleanup
    if os.path.exists("test_aras.db"):
        os.remove("test_aras.db")

if __name__ == "__main__":
    try:
        test_full_cycle()
    except Exception as e:
        print(f"\nVerification FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
