from ..app import ERP
from ..app import ERP
from .models import PotSession, PotOrder, PotOrderLine, PotTerminal, PotPaymentLine
from . import views # Trigger view registration

class POT(ERP):
    app_name = "erp_pot"
    app_type = "module"
    app_label = "Point of Transaction"
    icon = "CreditCard"
    
    models = [PotTerminal, PotSession, PotOrder, PotOrderLine, PotPaymentLine]

    
    menu_groups = [
        {
            "label": "Master",
            "icon": "Database",
            "models": ["erp_pot_terminals"]
        },
        {
            "label": "Retail",
            "icon": "ShoppingBag",
            "models": ["erp_pot_sessions", "erp_pot_orders"]
        }
    ]

