import requests
from arasCore import create_app
from arasCore.lib.core.extensions import db

app = create_app()
with app.app_context():
    from flask_login import login_user
    from arasCore.admin.models import User
    user = User.query.first()
    print("Found user:", user.email if user else "None")
    
    with app.test_client() as client:
        if user:
            # force login
            with client.session_transaction() as sess:
                sess['_user_id'] = str(user.id)
                sess['_fresh'] = True
        resp = client.get('/admin/api/ui/init')
        print("Status:", resp.status_code)
        if resp.status_code == 200:
            print(resp.json)
        else:
            print("Error data:", resp.data)
