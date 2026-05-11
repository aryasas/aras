from run import app
with app.test_client() as client:
    # First, let's just do a direct DB query bypassing auth/session
    with app.app_context():
        from app.erp.erp_crm.models.customer import CrmCustomer
        print(f"Direct DB count: {CrmCustomer.query.count()}")
        print(f"First DB customer: {CrmCustomer.query.first()}")
        
        # Now let's test the API endpoint
        # We'll use the test client. 
        # But we need auth. Let's see what the API returns without auth.
    res = client.get('/api/erp/crm/customer/')
    print(f"API status without auth: {res.status_code}")
