import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from app import create_app
from arasCore.lib.core.extensions import db
from app.erp.erp_acc.models.invoice import AccSalesInvoice
from arasCore.admin.services import _get_child_tables_for_model
import json

app = create_app()
with app.app_context():
    cts = _get_child_tables_for_model(AccSalesInvoice)
    for ct in cts:
        print(f"Child Table: {ct['title']} ({ct['model_name']})")
        for col in ct.get('inline_columns', []):
            if 'product' in col['name']:
                print(f"  Column: {col['name']}")
                print(f"    Type: {col['type']}")
                print(f"    FK Table: {col['fk_table']}")
                print(f"    FK API URL: {col['fk_api_url']}")
                print(f"    FK Options Count: {len(col.get('fk_options', []))}")
                if len(col.get('fk_options', [])) > 0:
                    print(f"    First Option: {col['fk_options'][0]}")
