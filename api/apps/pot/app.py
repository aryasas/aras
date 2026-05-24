from core import Aras
from .models import PotSession, PotTerminal
from .routers import router as _sessions_router
from . import views  # noqa

class POT(Aras.App):
    app_name = "pot"
    table_prefix = "erp_pot"
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

