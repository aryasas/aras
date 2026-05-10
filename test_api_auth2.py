import json
from run import app
from arasCore.auth import User
from flask_login import login_user

with app.test_client() as client:
    with app.app_context():
        user = User.query.filter_by(is_active=True).first()
        if not user:
            print("No active user.")
            exit(1)
            
    # Login via post
    res = client.post('/admin/login/', data={'username': user.username, 'password': 'password'}) # We don't know the password, actually let's try to bypass auth.
    
    # Bypass auth by mocking current_user
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        
    res = client.get('/api/erp/crm/customer/')
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.get_json()
        print(f"Data length: {len(data.get('data', []))}")
        if data.get('data'):
            print(f"First item keys: {list(data['data'][0].keys())}")
    else:
        print(f"Response: {res.text}")
