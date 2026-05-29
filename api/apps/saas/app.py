from core.base.app import App
from core.logic.discovery import autodiscover_models
from .models import *
from . import views
from .routers import router
from .routers.payments import router as payments_router
from .routers.billing import router as billing_router
from .routers.admin import router as admin_router
from .payments.registry import PaymentProviderRegistry
from .payments.stripe_provider import StripeProvider
from .payments.midtrans_provider import MidtransProvider
from .payments.xendit_provider import XenditProvider

# Register providers
PaymentProviderRegistry.register(StripeProvider())
PaymentProviderRegistry.register(MidtransProvider())
PaymentProviderRegistry.register(XenditProvider())

class SaaSApp(App):
    app_name = "saas"
    app_label = "SaaS Control Plane"
    icon = "Cloud"
    have_home = True
    routers = [router, payments_router, billing_router, admin_router]
    models = autodiscover_models(__name__, ["models"])

    @classmethod
    def seed(cls, db):
        from .plans import seed_default_plans
        seed_default_plans(db)

        # Seed default payment methods
        if not db.query(PaymentMethod).first():
            db.add(PaymentMethod(code="stripe_card", label="Credit/Debit Card", provider_code="stripe", icon="CreditCard", sort_order=1))
            db.commit()
