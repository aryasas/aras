from run import app
with app.test_request_context('/api/erp/crm/customer/'):
    from arasCore.lib.services.api_handler import _api_registry
    res = _api_registry.get('erp/crm/customer')
    print(res)
    # mock a request
    # actually, we can just use test client
with app.test_client() as client:
    # login first
    client.post('/admin/login/', data={'username': 'admin', 'password': 'password'}) # guess or just bypass auth
    response = client.get('/api/erp/crm/customer/')
    print(response.json)
