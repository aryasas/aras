
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("ARAS_MODE", "development")

from arasCore import create_app
app = create_app()

with app.app_context():
    from arasCore.admin.crud_factory import _get_child_tables_for_model
    from app.erp.erp_acc.models.invoice import AccSalesInvoice
    
    print(f"Testing for AccSalesInvoice...")
    cts = _get_child_tables_for_model(AccSalesInvoice)
    print(f"Found {len(cts)} child tables.")
    for ct in cts:
        print(f" - {ct['title']} (model_name: {ct['model_name']}, fk_col: {ct['fk_col']})")
        print(f"   vcols: {ct['vcols']}")
