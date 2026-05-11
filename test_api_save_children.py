
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("ARAS_MODE", "development")

from arasCore import create_app
from arasCore.lib.core.extensions import db
app = create_app()

with app.app_context():
    from app.erp.erp_acc.models.invoice import AccSalesInvoice, AccSalesInvoiceLine
    from app.erp.erp_crm.models.customer import CrmCustomer
    from app.erp.erp_config.models.company import Company
    
    # Get or create a customer
    cust = CrmCustomer.query.first()
    if not cust:
        cust = CrmCustomer(name="Test Customer")
        db.session.add(cust)
    
    comp = Company.query.first()
    if not comp:
        comp = Company(name="Test Company", slug="test")
        db.session.add(comp)
    
    db.session.commit()

    # Create an invoice
    inv = AccSalesInvoice(customer_id=cust.id, company_id=comp.id, number="INV-TEST-001")
    db.session.add(inv)
    db.session.commit()
    
    inv_id = inv.id
    print(f"Created Invoice ID: {inv_id}")

    # Now simulate a PUT request to update it with lines
    from arasCore.lib.services.api_handler import _api_registry
    # We need to simulate the environment
    from flask import request
    
    # We'll just call the logic that's in api_handler.py manually for testing
    data = {
        "number": "INV-TEST-001-UPDATED",
        "acc_sales_invoice_line": [
            {"description": "Item 1", "qty": 1, "unit_price": 100},
            {"description": "Item 2", "qty": 2, "unit_price": 50}
        ]
    }
    
    print(f"Updating invoice with data: {data}")
    
    # Logic from api_handler.py (PUT)
    inv = AccSalesInvoice.query.get(inv_id)
    for col in inv.__table__.columns:
        if col.name != "id" and col.name in data:
            setattr(inv, col.name, data[col.name])
    
    # Check if lines were updated (they won't be in the current implementation)
    db.session.commit()
    
    inv = AccSalesInvoice.query.get(inv_id)
    print(f"Updated Number: {inv.number}")
    print(f"Number of lines: {len(inv.lines)}")
    
    if len(inv.lines) == 0:
        print("CONFIRMED: Child tables are NOT saved by the default Universal API implementation.")
