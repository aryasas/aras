from ..app import ERP
from . import views # Trigger view registration

from core.logic.discovery import autodiscover_models
from .models import * # Import all models for discovery
from .services import posting as _posting  # noqa: F401 — registers on_transition callbacks

class Stock(ERP):
    app_name = "erp_stock"
    app_type = "module"
    app_label = "Stock"
    icon = "Package"

    models = autodiscover_models(__name__, ["models"])

    menu_groups = [
        {
            "label": "Master Data",
            "icon": "Database",
            "models": ["erp_stock_items", "erp_stock_categories", "erp_stock_locations"]
        },
        {
            "label": "Operations",
            "icon": "Truck",
            "models": ["erp_stock_delivery_notes", "erp_stock_movements"]
        },
        {
            "label": "Pricing & Promo",
            "icon": "Tag",
            "models": ["erp_stock_pricelists", "erp_stock_promo_bundles"]
        }
    ]

