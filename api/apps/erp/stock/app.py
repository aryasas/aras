from ..app import ERP
from . import views # Trigger view registration

from core.logic.discovery import autodiscover_models
from .models import * # Import all models for discovery
from .models_valuation import * # Import all models from models_valuation for discovery

class Stock(ERP):
    app_name = "erp_stock"
    app_label = "Stock"
    icon = "Package"

    models = autodiscover_models(__name__, [
        "models", "models_valuation"
    ])

    menu_groups = [
        {
            "label": "Master Data",
            "icon": "Database",
            "models": ["erp_stock_products", "erp_stock_categories", "erp_stock_locations"]
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

