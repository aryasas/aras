import sys
sys.path.insert(0, '.')
from app import create_app
app = create_app()
app.testing = True
client = app.test_client()

with app.app_context():
    # Attempt to grab the page by bypassing login using test_client session or directly hitting the URL.
    # But wait, we need to login as admin.
    resp = client.post('/admin/login/', data={'username': 'admin', 'password': 'password'}, follow_redirects=True)
    resp = client.get('/admin/erp/product/edit/11/')
    with open('test_out.html', 'wb') as f:
        f.write(resp.data)
