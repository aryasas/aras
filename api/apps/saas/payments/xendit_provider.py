# gemini-2-5-flash
import os
import os
from typing import Optional, List, Dict, Any
from .base import PaymentProvider, Checkout, WebhookEvent
import xendit
from core import Aras

class XenditProvider(PaymentProvider):
    code = "xendit"
    label = "Xendit"
    countries = ["ID", "PH", "MY", "TH", "VN"]

    def __init__(self):
        xendit.api_key = os.getenv("XENDIT_SECRET_KEY")
        self.webhook_token = os.getenv("XENDIT_WEBHOOK_TOKEN")

    def create_checkout(self, subscription: Any, amount: float, currency: str, return_url: str) -> Checkout:
        # xendit-python 0.x style
        invoice = xendit.Invoice.create(
            external_id=f"SUB-{subscription.id}-{int(os.times()[4])}",
            amount=float(amount),
            currency=currency,
            success_redirect_url=return_url,
            payer_email=subscription.email,
            description=f"Subscription: {subscription.company_name}"
        )
        return Checkout(id=invoice.id, url=invoice.invoice_url)

    def verify_webhook(self, headers: Dict[str, str], raw_body: bytes) -> WebhookEvent:
        import json
        callback_token = headers.get("x-callback-token")
        webhook_token = self.webhook_token or os.getenv("XENDIT_WEBHOOK_TOKEN")
        if not webhook_token:
            raise ValueError("XENDIT_WEBHOOK_TOKEN not set")

        if callback_token != webhook_token:
            raise ValueError("Xendit callback token verification failed")
            
        data = json.loads(raw_body)
        status = "pending"
        xendit_status = data.get("status")
        if xendit_status == "PAID":
            status = "succeeded"
        elif xendit_status == "EXPIRED":
            status = "failed"

        # Parse sub_id from external_id: SUB-{sub_id}-{ts}
        external_id = data.get("external_id")
        subscription_id = None
        if external_id and external_id.startswith("SUB-"):
            parts = external_id.split("-")
            if len(parts) >= 2:
                subscription_id = parts[1]

        return WebhookEvent(
            event_type=xendit_status,
            payment_id=data.get("id"),
            status=status,
            raw_data=data,
            subscription_id=int(subscription_id) if subscription_id else None,
            amount=float(data.get("amount")) if data.get("amount") else None,
            currency=data.get("currency", "IDR").upper()
        )

    def refund(self, payment_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        return {"status": "unsupported", "message": "Refund via Invoice API not directly supported"}

    def list_methods(self, country: Optional[str] = None) -> List[Dict[str, Any]]:
        return [
            {"code": "va", "label": "Virtual Account", "icon": "Landmark"},
            {"code": "qris", "label": "QRIS", "icon": "QrCode"},
            {"code": "ewallet", "label": "E-Wallet", "icon": "Wallet"},
        ]
