# gemini-2-5-flash
import stripe
import os
from typing import Optional, List, Dict, Any
from .base import PaymentProvider, Checkout, WebhookEvent

class StripeProvider(PaymentProvider):
    code = "stripe"
    label = "Stripe"
    countries = ["*"]

    def __init__(self):
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    def create_checkout(self, subscription: Any, amount: float, currency: str, return_url: str) -> Checkout:
        # stripe>=8 syntax
        session = stripe.checkout.Session.create(
            payment_method_types=["card", "link", "sepa_debit", "us_bank_account", "klarna", "apple_pay", "google_pay"],
            line_items=[{
                "price_data": {
                    "currency": currency.lower(),
                    "product_data": {
                        "name": f"Subscription: {subscription.company_name}",
                    },
                    "unit_amount": int(amount * 100), # Stripe uses cents
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=return_url + "?status=success&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=return_url + "?status=cancelled",
            client_reference_id=str(subscription.id),
            metadata={
                "subscription_id": str(subscription.id)
            }
        )
        return Checkout(id=session.id, url=session.url)

    def verify_webhook(self, headers: Dict[str, str], raw_body: bytes) -> WebhookEvent:
        sig_header = headers.get("stripe-signature")
        webhook_secret = self.webhook_secret or os.getenv("STRIPE_WEBHOOK_SECRET")
        if not webhook_secret:
            raise ValueError("STRIPE_WEBHOOK_SECRET not set")
            
        try:
            event = stripe.Webhook.construct_event(
                raw_body, sig_header, webhook_secret
            )
        except Exception as e:
            raise ValueError(f"Stripe webhook verification failed: {str(e)}")

        status = "unknown"
        payment_id = None
        subscription_id = None
        amount = None
        currency = None
        
        if event["type"] == "checkout.session.completed":
            status = "succeeded"
            obj = event["data"]["object"]
            payment_id = obj["id"]
            subscription_id = obj.get("client_reference_id") or obj.get("metadata", {}).get("subscription_id")
            amount = obj.get("amount_total", 0) / 100.0
            currency = obj.get("currency", "").upper()
        elif event["type"] == "payment_intent.payment_failed":
            status = "failed"
            obj = event["data"]["object"]
            payment_id = obj["id"]
            subscription_id = obj.get("metadata", {}).get("subscription_id")
            amount = obj.get("amount_received", 0) / 100.0
            currency = obj.get("currency", "").upper()

        return WebhookEvent(
            event_type=event["type"],
            payment_id=payment_id,
            status=status,
            raw_data=event,
            subscription_id=int(subscription_id) if subscription_id else None,
            amount=amount,
            currency=currency
        )

    def refund(self, payment_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        params = {"payment_intent": payment_id}
        if amount:
            params["amount"] = int(amount * 100)
        return stripe.Refund.create(**params)

    def list_methods(self, country: Optional[str] = None) -> List[Dict[str, Any]]:
        return [
            {"code": "card", "label": "Credit/Debit Card", "icon": "CreditCard"},
            {"code": "apple_pay", "label": "Apple Pay", "icon": "Apple"},
            {"code": "google_pay", "label": "Google Pay", "icon": "Google"},
        ]
