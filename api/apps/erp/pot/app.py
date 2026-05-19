from ..app import ERP
from .models import PotSession, PotTerminal
from .routers import router as _sessions_router
from . import views  # noqa

class POT(ERP):
    app_name = "erp_pot"
    app_type = "module"
    app_label = "Point of Transaction"
    icon = "CreditCard"

    models = [PotTerminal, PotSession]
    routers = [_sessions_router]

    
    menu_groups = [
        {
            "label": "Master",
            "icon": "Database",
            "models": ["erp_pot_terminals"]
        },
        {
            "label": "Retail",
            "icon": "ShoppingBag",
            "models": ["erp_pot_sessions"]
        }
    ]

