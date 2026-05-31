from core import Aras
from .routers import router as _sessions_router
from . import views  # noqa

from core.registry.config_registry import ConfigSection, ConfigField
from core.registry.master_data_registry import MasterEntity
from .models import PotSession, PotTerminal

class POT(Aras.App):
    app_name = "pot"
    app_label = "Point of Transaction"
    icon = "CreditCard"
    saas_module = "pos"

    master_data = [
        MasterEntity(key="pot_terminal", model=PotTerminal, scope="module", icon="Monitor", order=10),
    ]

    config_sections = [
        ConfigSection(key="general", label="General", scope="module", fields=[
            ConfigField(key="receipt_footer", type="text", default="Thank you for your purchase!", label="Receipt Footer"),
            ConfigField(key="enable_cash_drawer", type="bool", default=True, label="Enable Cash Drawer"),
            ConfigField(key="tax_inclusive_prices", type="bool", default=False, label="Tax-Inclusive Prices"),
            ConfigField(key="default_tender", type="choice", default="cash", label="Default Tender",
                        choices=[("cash", "Cash"), ("card", "Card"), ("qr", "QR Pay")]),
        ]),
        ConfigSection(key="printing", label="Printing", scope="module", fields=[
            ConfigField(key="auto_print_receipt", type="bool", default=True, label="Auto-Print Receipt"),
            ConfigField(key="printer_name", type="string", label="Printer Name"),
        ]),
    ]

    models = [PotTerminal, PotSession]
    routers = [_sessions_router]

    
    menu_groups = [
        {
            "label": "Master",
            "icon": "Database",
            "models": ["pot_terminals"]
        },
        {
            "label": "Retail",
            "icon": "ShoppingBag",
            "models": ["pot_sessions"],
            "links": [
                {"name": "pos", "label": "Point of Sale", "path": "/pot/pos", "icon": "CreditCard"},
            ],
        }
    ]

