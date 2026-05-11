import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from arasCore import create_app
from arasCore.admin.models import AppManagerTable, AppManagerColumn

app = create_app()
with app.app_context():
    # Try different name variants
    names = ['erp/acc/sales-invoice', 'sales-invoice', 'acc_sales_invoice']
    t = None
    for name in names:
        t = AppManagerTable.query.filter((AppManagerTable.name == name) | (AppManagerTable.db_table_name == name)).first()
        if t: break
        
    if t:
        print(f"Table: {t.title} (ID: {t.id})")
        for c in t.columns:
            print(f"  Col: {c.name} Type: {c.field_type} RelSys: {c.relation_system_table} RelTbl: {c.relation_table_id}")
            
        # Check child tables
        from arasCore.admin.services import _get_child_tables_for_model
        from app.erp.erp_acc.models.invoice import AccSalesInvoice
        cts = _get_child_tables_for_model(AccSalesInvoice)
        for ct in cts:
            print(f"Child Table: {ct['title']} ({ct['model_name']})")
            # Check if this child table itself is registered in AppManager
            ct_t = AppManagerTable.query.filter((AppManagerTable.name == ct['model_name']) | (AppManagerTable.db_table_name == ct['model_name'])).first()
            if ct_t:
                print(f"  Child Table registered in AppManager (ID: {ct_t.id})")
                for c in ct_t.columns:
                    print(f"    Col: {c.name} Type: {c.field_type} RelSys: {c.relation_system_table} RelTbl: {c.relation_table_id}")
            else:
                print("  Child Table NOT registered in AppManager")
    else:
        print("Sales Invoice table not found in AppManagerTable")
