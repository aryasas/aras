import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARAS_CONFIG", "development")
from arasCore import create_app
from arasCore.lib.core.extensions import db
from werkzeug.security import generate_password_hash
import traceback

app = create_app()
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

with app.test_client() as client:
    with app.app_context():
        from arasCore.auth import User
        user = User.query.filter_by(username="admin").first()
        if not user:
            user = User(username="admin", password_hash=generate_password_hash("admin"), is_active=True, email="admin@example.com")
            db.session.add(user)
            db.session.commit()
    
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True

    try:
        # First get the existing ID of UOM 1 for product 11
        with app.app_context():
            from aras.erp.erp_stock.models.product import StockProductUom
            uom = StockProductUom.query.filter_by(product_id=11, uom_id=1).first()
            uom_id = uom.id if uom else ""

        # Simulate form data without id (INSERT)
        response = client.post('/admin/api/child-table/stock_product_uom/save?parent_model=stock_product&li=stock_product_uom&fk_col=product_id&parent_id=11', data={
            "id": "", # empty ID
            "product_id": "11",
            "uom_id": "4", # different uom_id
            "factor": "5.5", # valid factor
            "barcode": "888"
        })
        print("STATUS:", response.status_code)
        print("DATA:", response.get_data(as_text=True))
    except Exception as e:
        traceback.print_exc()
