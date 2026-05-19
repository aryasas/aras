from core import Aras
from .models import Plan, Subscription, LicenseToken, ActivationRequest


class PlanView(Aras.View):
    model = Plan
    title = "Plans"
    icon = "pi pi-tag"


class SubscriptionView(Aras.View):
    model = Subscription
    title = "Subscriptions"
    icon = "pi pi-users"


class LicenseTokenView(Aras.View):
    model = LicenseToken
    title = "License Tokens"
    icon = "pi pi-key"


class ActivationRequestView(Aras.View):
    model = ActivationRequest
    title = "Activation Requests"
    icon = "pi pi-inbox"
