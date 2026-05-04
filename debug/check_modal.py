import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ARAS_CONFIG", "development")
from arasCore import create_app
from arasCore.lib.core.extensions import db

app = create_app()
with app.app_context():
    # Import all models to satisfy SQLAlchemy string relationships
    from aras.erp.erp_acc.models import account, journal, payment
    from aras.erp.erp_stock.models import product, stock, uom, location
    from aras.erp.erp_crm.models import crm
    from aras.erp.erp_sup.models import purchase
    
    from arasCore.admin.crud_factory import _get_child_tables_for_model
    from aras.erp.erp_stock.models.product import StockProduct
    
    tabs = _get_child_tables_for_model(StockProduct)
    for t in tabs:
        if t["model_name"] == "stock_product_uom":
            print("VCOLS:", [v['name'] for v in t['vcols']])
            # print("REQUIRED:", [v['name'] for v in t['vcols'] if not v['col'].nullable])
