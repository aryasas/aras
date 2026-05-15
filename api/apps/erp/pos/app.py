from ..app import ERP
from .models import PosSession, PosOrder, PosOrderLine, PosTerminal, PosPaymentLine
from . import views # Trigger view registration

class POS(ERP):
    app_name = "erp_pos"
    app_label = "POS"
    icon = "CreditCard"
    
    models = [PosTerminal, PosSession, PosOrder, PosOrderLine, PosPaymentLine]

    
    menu_groups = [
        {
            "label": "Master",
            "icon": "Database",
            "models": ["erp_pos_terminals"]
        },
        {
            "label": "Retail",
            "icon": "ShoppingBag",
            "models": ["erp_pos_sessions", "erp_pos_orders"]
        }
    ]

