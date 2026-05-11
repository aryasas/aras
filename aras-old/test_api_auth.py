import json
from run import app
from arasCore.admin.models import User
from flask_login import login_user

with app.test_client() as client:
    with app.app_context():
        user = User.query.filter_by(is_active=True).first()
        if not user:
            print("No active user.")
            exit(1)
        # Login using the test client
        with client.session_transaction() as sess:
            # Bypass Flask-Login complexities for test client by just hitting a login route or setting session
            pass
            
    # Actually, the easiest way to test the API with auth is to post to /admin/login/
    res = client.post('/admin/login/', data={'username': 'admin', 'password': 'password'})
    
    # Now call the API
    res = client.get('/api/erp/crm/customer/')
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.get_json()
        print(f"Data length: {len(data.get('data', []))}")
        if data.get('data'):
            print(f"First item keys: {list(data['data'][0].keys())}")
    else:
        print(f"Response: {res.text}")
