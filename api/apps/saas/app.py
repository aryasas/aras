from core.base.app import App
from core.logic.discovery import autodiscover_models
from .models import *
from . import views
from .routers import router
from .routers.payments import router as payments_router
from .routers.billing import router as billing_router
from .routers.control_panel import router as control_panel_router
from .payments.registry import PaymentProviderRegistry
from .payments.stripe_provider import StripeProvider
from .payments.midtrans_provider import MidtransProvider
from .payments.xendit_provider import XenditProvider

# Register providers
PaymentProviderRegistry.register(StripeProvider())
PaymentProviderRegistry.register(MidtransProvider())
PaymentProviderRegistry.register(XenditProvider())

from core.registry.config_registry import ConfigSection, ConfigField

class SaaSApp(App):
    app_name = "saas"
    app_label = "SaaS Control Panel"
    app_type = "platform"
    icon = "Cloud"
    have_home = True
    config_sections = [
        ConfigSection(key="general", label="General", scope="module", fields=[
            ConfigField(key="trial_days", type="number", default=14, label="Trial Period (days)"),
            ConfigField(key="default_plan", type="string", default="free", label="Default Plan on Signup"),
            ConfigField(key="signup_open", type="bool", default=True, label="Public Signup Open"),
            ConfigField(key="require_email_verification", type="bool", default=True, label="Require Email Verification"),
        ]),
        ConfigSection(key="billing", label="Billing", scope="module", fields=[
            ConfigField(key="grace_period_days", type="number", default=3, label="Payment Grace Period (days)"),
            ConfigField(key="auto_suspend_overdue", type="bool", default=True, label="Auto-Suspend Overdue Tenants"),
            ConfigField(key="stripe_publishable_key", type="string", label="Stripe Publishable Key"),
            ConfigField(key="stripe_secret_key", type="secret", label="Stripe Secret Key", secret=True),
        ]),
    ]
    routers = [router, payments_router, billing_router]
    models = autodiscover_models(__name__, ["models"])
    jobs = [
        {
            "key": "billing-daily",
            "schedule_cron": "0 2 * * *",
            "handler_path": "apps.saas.cron.billing_job",
            "enabled_default": True,
        }
    ]

    @classmethod
    def register_services(cls):
        from core.service_registry import ServiceRegistry
        from .services.license_service import LicenseService
        from .models import Plan, Subscription
        ServiceRegistry.register("LicenseService", LicenseService)
        ServiceRegistry.register("Plan", Plan)
        ServiceRegistry.register("Subscription", Subscription)

    @classmethod
    def seed(cls, db):
        from .plans import seed_default_plans
        seed_default_plans(db)

        # Seed default payment methods
        if not db.query(PaymentMethod).first():
            db.add(PaymentMethod(code="stripe_card", label="Credit/Debit Card", provider_code="stripe", icon="CreditCard", sort_order=1))
            db.commit()
