from run import app
from arasCore.auth import User
with app.test_client() as c:
    with app.app_context():
        user = User.query.first()
    with c.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True
    res = c.get("/admin/erp/main/doc-series/")
    with open("out.html", "w") as f:
        f.write(res.data.decode())
    print("Status:", res.status_code)
