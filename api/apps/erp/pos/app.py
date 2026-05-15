from core import Aras
from .models import PosSession, PosOrder, PosOrderLine
from . import views # Trigger view registration

class PosApp(Aras.App):
    app_name = "erp_pos"
    parent_name = "erp"
    app_label = "Point of Sale"
    icon = "ShoppingCart"
    
    models = [PosSession, PosOrder, PosOrderLine]
    
    menu_groups = [
        {
            "label": "POS Operations",
            "icon": "ShoppingCart",
            "models": ["erp_pos_sessions", "erp_pos_orders"]
        }
    ]
