from ..app import ERP
from .models import Supplier
from . import views # Trigger view registration

class Supplier(ERP):
    app_name = "erp_supplier"
    app_label = "Suppliers"
    icon = "Truck"
    
    models = [Supplier]
    
    menu_groups = [
        {
            "label": "Suppliers",
            "icon": "Truck",
            "models": ["erp_supplier_suppliers"]
        }
    ]
