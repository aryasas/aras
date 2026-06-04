from core import Aras
from . import views  # Trigger view registration
from core.auth.access import UserAccess
from .rbac_router import access_router

from core.logic.discovery import autodiscover_models
# Workspace primitives (Organization/Currency/PrintTemplate/Notification) are
# framework-tier now (core.workspace) and registered there; we only reference
# them for product-side master_data/menu presentation.
from core.workspace.models import Organization, Currency, PrintTemplate, Notification
from plugins.commerce.models import Uom, PriceType, Charge, ExchangeRate, ModeOfPayment, OrganizationPaymentAccount
from core.registry.series import Series # Import Series directly, autodiscovery will pick it up if it's an ArasModel
from core.registry.master_data_registry import MasterEntity
from core.seeds import RbacSeed, SeriesSeed
from .seed_rbac import seed_access
from .seeds.standard import seed_trade_payment_accounts

class Config(Aras.App):
    app_name = "settings"
    app_label = "Settings"
    app_type = "app"
    required = True
    hide_from_sidebar = True

    routers = [access_router]

    models = autodiscover_models("core.registry", ["series"]) + [UserAccess] + [
        # commerce plugin primitives surfaced through the config app's UI/menus
        Uom, PriceType, Charge, ExchangeRate, ModeOfPayment, OrganizationPaymentAccount,
    ]

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
            "models": ["core_organizations", "core_currencies", "config_exchange_rates"]
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
                "core_workflow_templates",
                "core_workflow_states",
                "core_workflow_transitions",
                "core_workflow_actions",
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
            "models": ["core_print_templates", "core_notifications"]
        },
    ]

    @classmethod
    def register_services(cls):
        from core.service_registry import ServiceRegistry
        from .rbac import get_access, get_user_org_list
        # Organization/Notification registered framework-side (core.workspace).
        ServiceRegistry.register("get_access", get_access)
        ServiceRegistry.register("get_user_org_list", get_user_org_list)

    # Declarative seeds (generic framework runner; data co-located in apps/settings/seeds/).
    # Order matters: RBAC roles first, then the role/admin wiring, then numbering series.
    seeds = [
        RbacSeed("seeds/roles.yaml"),
        seed_access,
        SeriesSeed("seeds/series.yaml"),
        seed_trade_payment_accounts,
    ]
