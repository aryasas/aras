# gemini-flash
from .master_data_registry import master_data_registry, MasterEntity

def register_core_entities():
    """
    Registers framework-level shared master data entities.
    Uses late imports to avoid circular dependency with Aras facade during initialization.
    """
    from apps.config.models import (
        Organization, Currency, Uom, ExchangeRate, 
        PriceType, Charge, ModeOfPayment, PrintTemplate, Notification
    )

    # Shared entities owned by the framework but implemented in apps/config
    master_data_registry.register_entity("core", MasterEntity(
        key="organization", 
        model=Organization, 
        label="Organizations",
        icon="Building2", 
        scope="shared", 
        order=10
    ))

    master_data_registry.register_entity("core", MasterEntity(
        key="currency", 
        model=Currency, 
        label="Currencies",
        icon="Coins", 
        scope="shared", 
        order=20
    ))

    master_data_registry.register_entity("core", MasterEntity(
        key="uom", 
        model=Uom, 
        label="Units of Measure",
        icon="Scale", 
        scope="shared", 
        order=30
    ))

    master_data_registry.register_entity("core", MasterEntity(
        key="exchange_rate", 
        model=ExchangeRate, 
        label="Exchange Rates",
        icon="RefreshCw", 
        scope="shared", 
        order=40
    ))

    master_data_registry.register_entity("core", MasterEntity(
        key="price_type", 
        model=PriceType, 
        label="Price Types",
        icon="Tag", 
        scope="shared", 
        order=50
    ))

    master_data_registry.register_entity("core", MasterEntity(
        key="charge", 
        model=Charge, 
        label="Taxes & Charges",
        icon="Percent", 
        scope="shared", 
        order=60
    ))

    master_data_registry.register_entity("core", MasterEntity(
        key="payment_mode", 
        model=ModeOfPayment, 
        label="Modes of Payment",
        icon="CreditCard", 
        scope="shared", 
        order=70
    ))

    master_data_registry.register_entity("core", MasterEntity(
        key="print_template", 
        model=PrintTemplate, 
        label="Print Templates",
        icon="Printer", 
        scope="shared", 
        order=80
    ))

    master_data_registry.register_entity("core", MasterEntity(
        key="notification", 
        model=Notification, 
        label="Notifications",
        icon="Bell", 
        scope="shared", 
        order=90
    ))
