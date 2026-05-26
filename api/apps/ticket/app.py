# gemini-flash
from core import Aras
from core.logic.discovery import autodiscover_models

class TicketingApp(Aras.App):
    app_name = "ticket"
    table_prefix = "erp_ticket"
    app_label = "Ticketing"
    icon = "Ticket"
    
    # Import models and views for side-effect registration
    from . import models, views # noqa: F401
    
    models = autodiscover_models(__name__, ["models"])
    
    menu_groups = [
        {
            "label": "Operations",
            "icon": "Ticket",
            "models": [
                "erp_ticket_tickets",
                "erp_ticket_teams",
                "erp_ticket_categories"
            ]
        }
    ]
