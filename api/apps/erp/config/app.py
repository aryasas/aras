from core import Aras
from .models import Company, Currency, Uom, PriceType
from . import views # Trigger view registration

class ErpConfigApp(Aras.App):
    app_name = "erp_config"
    parent_name = "erp"
    app_label = "ERP Configuration"
    icon = "Settings"
    
    models = [Company, Currency, Uom, PriceType]
    
    menu_groups = [
        {
            "label": "Master Data",
            "icon": "Database",
            "models": ["erp_config_companies", "erp_config_currencies", "erp_config_uoms", "erp_config_price_types"]
        }
    ]
