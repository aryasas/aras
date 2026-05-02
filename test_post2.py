import json
from run import app

with app.test_client() as client:
    from arasCore.auth import User
    with app.app_context():
        user = User.query.filter_by(username="admin").first()
        if not user:
            user = User.query.first()
        user_id = user.id

    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True

    # Note: no trailing slash here!
    res = client.post('/api/erp/acc/purchase-invoice/post', json={"invoice_id": 1})
    print("Status:", res.status_code)
    try:
        print("JSON:", res.json)
    except:
        print("Text:", res.text)
