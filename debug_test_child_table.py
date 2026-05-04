#!/usr/bin/env python3
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARAS_CONFIG", "development")

from arasCore import create_app
from werkzeug.security import generate_password_hash

app = create_app()
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

with app.test_client() as client:
    with app.app_context():
        from arasCore.auth import User
        user = User.query.filter_by(username="admin").first()
        if not user:
            user = User(username="admin", password_hash=generate_password_hash("admin"), is_active=True, email="admin@example.com")
            from arasCore.lib.core.extensions import db
            db.session.add(user)
            db.session.commit()
    
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True

    try:
        print("Testing child table save endpoint...")
        response = client.post('/admin/api/child-table/stock_product_uom/save?parent_model=stock_product&li=stock_product_uom&fk_col=product_id&parent_id=11', 
                             json={
                                 "product_id": "11", 
                                 "uom_id": "4", 
                                 "factor": "5.5", 
                                 "barcode": "888"
                             })
        print("STATUS:", response.status_code)
        print("DATA:", response.get_data(as_text=True))
        
        if response.status_code == 500:
            print("ERROR DETAILS:")
            # Get the error details from the response
            try:
                error_data = response.get_json()
                print("Error JSON:", error_data)
            except:
                print("Could not parse error as JSON")
                
    except Exception as e:
        import traceback
        print("EXCEPTION:", str(e))
        traceback.print_exc()
