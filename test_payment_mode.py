import sys
import traceback
from run import app

with app.app_context():
    with app.test_client() as client:
        # Assuming admin login
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'  # Flask-login requires string for user id
            sess['_fresh'] = True
            
        try:
            response = client.get('/admin/erp/payment-mode/', follow_redirects=True)
            print(f"Status: {response.status_code}")
            content = response.data.decode('utf-8')
            print("Content Snippet:")
            print(content[:500])
            if "Traceback" in content or "Exception" in content:
                print("FOUND ERROR IN RESPONSE!")
        except Exception as e:
            traceback.print_exc()
