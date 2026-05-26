from core import Aras
from .models import Plan, Subscription, LicenseToken, ActivationRequest


class PlanView(Aras.View):
    model = Plan
    title = "Plans"
    icon = "Tag"


# claude-opus-4-7
class SubscriptionView(Aras.View):
    model = Subscription
    title = "Subscriptions"
    icon = "Users"


class LicenseTokenView(Aras.View):
    model = LicenseToken
    title = "License Tokens"
    icon = "Key"


class ActivationRequestView(Aras.View):
    model = ActivationRequest
    title = "Activation Requests"
    icon = "Inbox"
