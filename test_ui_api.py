import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from arasCore import create_app
from arasCore.admin.models import AppManagerTable
from arasCore.admin.services import _get_child_tables_for_model
from app.erp.erp_acc.models.invoice import AccSalesInvoice
import json

app = create_app()
with app.app_context():
    # Simulate the logic in ui_resource_config
    model = AccSalesInvoice
    cts = _get_child_tables_for_model(model)
    
    child_tables_meta = []
    for ct in cts:
        columns_meta = []
        if "inline_columns" in ct:
            for c in ct["inline_columns"]:
                columns_meta.append({
                    "name": c["name"],
                    "label": c["label"],
                    "type": c["type"],
                    "required": c.get("required", False),
                    "fk_table": c.get("fk_table"),
                    "fk_api_url": c.get("fk_api_url"),
                    "fk_options": c.get("fk_options", [])
                })
        
        child_tables_meta.append({
            "name": ct["model_name"],
            "title": ct["title"],
            "columns": columns_meta
        })

    # Find the Product Line child table
    pl = next((c for c in child_tables_meta if c['name'] == 'acc_sales_invoice_line'), None)
    if pl:
        print(f"Metadata for {pl['name']}:")
        prod_col = next((c for c in pl['columns'] if c['name'] == 'product_id'), None)
        if prod_col:
            print(json.dumps(prod_col, indent=2))
        else:
            print("product_id column not found in metadata!")
    else:
        print("acc_sales_invoice_line child table not found!")
