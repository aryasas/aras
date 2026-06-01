from core import Aras
from . import views  # Trigger view registration
from .erp_rbac import ErpUserAccess
from .erp_rbac_router import erp_rbac_router
from .vocabulary_router import vocabulary_router

from core.logic.discovery import autodiscover_models
from .models import * # Import all models for discovery
from .workflow_models import * # Import all models from workflow_models for discovery
from core.registry.series import Series # Import Series directly, autodiscovery will pick it up if it's an ArasModel
from core.registry.master_data_registry import MasterEntity

class Config(Aras.App):
    app_name = "config"
    app_label = "Settings"
    app_type = "framework"
    required = True
    hide_from_sidebar = True

    routers = [erp_rbac_router, vocabulary_router]

    models = autodiscover_models(__name__, [
        "models", "workflow_models"
    ]) + autodiscover_models("core.registry", ["series"]) + [ErpUserAccess]

    master_data = [
        MasterEntity(key="organization", model=Organization, scope="shared", icon="Building2", order=10),
        MasterEntity(key="currency", model=Currency, scope="shared", icon="Coins", order=20),
        MasterEntity(key="uom", model=Uom, scope="shared", icon="Scale", order=30),
        MasterEntity(key="exchange_rate", model=ExchangeRate, scope="shared", icon="RefreshCw", order=40),
        MasterEntity(key="price_type", model=PriceType, scope="shared", icon="Tag", order=50),
        MasterEntity(key="charge", model=Charge, scope="shared", icon="Percent", order=60),
        MasterEntity(key="payment_mode", model=ModeOfPayment, scope="shared", icon="CreditCard", order=70),
        MasterEntity(key="print_template", model=PrintTemplate, scope="shared", icon="Printer", order=80),
        MasterEntity(key="notification", model=Notification, scope="shared", icon="Bell", order=90),
    ]

    menu_groups = [
        {"label": "Access Control", "icon": "ShieldCheck", "models": []},
        {
            "label": "System",
            "icon": "Cpu",
            "models": ["config_organizations", "config_currencies", "config_exchange_rates"]
        },
        {
            "label": "Finance Configuration",
            "icon": "Wallet",
            "models": ["config_payment_modes", "config_charges", "config_price_types"]
        },
        {
            "label": "Standards",
            "icon": "Box",
            "models": ["config_uoms"]
        },
        {
            "label": "Workflow",
            "icon": "GitBranch",
            "models": [
                "config_workflow_templates",
                "config_workflow_states",
                "config_workflow_transitions",
                "config_workflow_actions",
            ]
        },
        {
            "label": "Series",
            "icon": "Hash",
            "models": ["core_series"]
        },
        {
            "label": "System Tools",
            "icon": "Activity",
            "models": ["config_print_templates", "config_notifications"]
        },
    ]

    @classmethod
    def seed(cls, db):
        from .seed_rbac import run_seed as seed_rbac
        seed_rbac(db)
