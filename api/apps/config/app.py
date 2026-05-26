from core import Aras
from . import views  # Trigger view registration
from .erp_rbac import ErpUserAccess
from .erp_rbac_router import erp_rbac_router
from .vocabulary_router import vocabulary_router

from core.logic.discovery import autodiscover_models
from .models import * # Import all models for discovery
from .workflow_models import * # Import all models from workflow_models for discovery
from core.registry.series import Series # Import Series directly, autodiscovery will pick it up if it's an ArasModel

class Config(Aras.App):
    app_name = "config"
    table_prefix = "erp_config"

    routers = [erp_rbac_router, vocabulary_router]

    models = autodiscover_models(__name__, [
        "models", "workflow_models"
    ]) + autodiscover_models("core.registry", ["series"]) + [ErpUserAccess]

    menu_groups = [
        {"label": "Access Control", "icon": "ShieldCheck", "models": []},
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
            "models": ["doc_series"]
        },
        {
            "label": "System Tools",
            "icon": "Activity",
            "models": ["erp_config_print_templates", "erp_config_notifications"]
        },
    ]

    @classmethod
    def seed(cls, db):
        from .seed_rbac import run_seed as seed_rbac
        seed_rbac(db)
