import json
from run import app
from flask import request

with app.test_client() as client:
    # First login as admin
    from arasCore.auth import User
    with app.app_context():
        user = User.query.filter_by(username="admin").first()
        if not user:
            user = User.query.first()
        user_id = user.id

    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True

    res = client.post('/api/erp/acc/purchase-invoice/post/', json={"invoice_id": 1})
    print(res.status_code)
    try:
        print(res.json)
    except:
        print(res.text)
