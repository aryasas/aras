from app import create_app
from flask import json
from aras.erp.manifest import _handle_payment_load_invoices

app = create_app()
with app.app_context():
    # Simulate request for Payment ID 1 (which is Inbound but for Supplier 1)
    with app.test_request_context(
        path='/api/erp/acc/payment/load-invoices/',
        method='POST',
        data=json.dumps({'payment_id': 1}),
        content_type='application/json'
    ):
        resp = _handle_payment_load_invoices()
        print("Response for Payment ID 1 (Existing Inbound Supplier Payment):")
        print(resp.get_data(as_text=True))

    # Simulate request for a NEW payment for Supplier 1
    with app.test_request_context(
        path='/api/erp/acc/payment/load-invoices/',
        method='POST',
        data=json.dumps({
            'partner_id': 1,
            'partner_type': 'supplier',
            'total_amount': 500000
        }),
        content_type='application/json'
    ):
        resp = _handle_payment_load_invoices()
        print("\nResponse for NEW payment (Supplier 1, Amount 500,000):")
        print(resp.get_data(as_text=True))
