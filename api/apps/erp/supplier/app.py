from core import Aras
from .models import Supplier
from . import views # Trigger view registration

class SupplierApp(Aras.App):
    app_name = "erp_supplier"
    parent_name = "erp"
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
