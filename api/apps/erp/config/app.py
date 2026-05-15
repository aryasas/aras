from ..app import ERP
from .models import Company, Currency, Uom, PriceType, Charge, ExchangeRate, Setting, ModeOfPayment, CompanyPaymentAccount, PrintTemplate, Notification
from . import views # Trigger view registration

class Config(ERP):
    app_name = "erp_config"
    app_label = "ERP Settings"
    icon = "Settings"

    models = [Company, Currency, Uom, PriceType, Charge, ExchangeRate, Setting, ModeOfPayment, CompanyPaymentAccount, PrintTemplate, Notification]

    menu_groups = [
        {
            "label": "System",
            "icon": "Cpu",
            "models": ["erp_config_companies", "erp_config_currencies", "erp_config_exchange_rates", "erp_config_settings"]
        },
        {
            "label": "Finance Configuration",
            "icon": "Wallet",
            "models": ["erp_config_payment_modes", "erp_config_charges", "erp_config_price_types"]
        },
        {
            "label": "Standards",
            "icon": "Box",
            "models": ["erp_config_uoms"]
        },
        {
            "label": "System Tools",
            "icon": "Activity",
            "models": ["erp_config_print_templates", "erp_config_notifications"]
        }
    ]

