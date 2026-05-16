from ..app import ERP
from . import views  # Trigger view registration

from core.logic.discovery import autodiscover_models
from .models import * # Import all models for discovery
from .workflow_models import * # Import all models from workflow_models for discovery
from core.registry.series import Series # Import Series directly, autodiscovery will pick it up if it's an ArasModel

class Config(ERP):
    app_name = "erp_config"
    app_label = "ERP Settings"
    icon = "Settings"

    models = autodiscover_models(__name__, [
        "models", "workflow_models"
    ]) + autodiscover_models("core.registry", ["series"])

    menu_groups = [
        {
            "label": "System",
            "icon": "Cpu",
            "models": ["erp_config_organizations", "erp_config_currencies", "erp_config_exchange_rates", "erp_config_settings"]
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
            "label": "Workflow",
            "icon": "GitBranch",
            "models": [
                "erp_config_workflow_templates",
                "erp_config_workflow_states",
                "erp_config_workflow_transitions",
                "erp_config_workflow_actions",
            ]
        },
        {
            "label": "Series",
            "icon": "Hash",
            "models": ["aras_naming_series"]
        },
        {
            "label": "System Tools",
            "icon": "Activity",
            "models": ["erp_config_print_templates", "erp_config_notifications"]
        },
    ]
