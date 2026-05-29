# gemini-2-5-flash
import os
import hashlib
from typing import Optional, List, Dict, Any
from .base import PaymentProvider, Checkout, WebhookEvent
import midtransclient
from core import Aras

class MidtransProvider(PaymentProvider):
    code = "midtrans"
    label = "Midtrans"
    countries = ["ID"]

    def __init__(self):
        self.server_key = os.getenv("MIDTRANS_SERVER_KEY")
        self.client_key = os.getenv("MIDTRANS_CLIENT_KEY")
        self.is_production = os.getenv("MIDTRANS_IS_PRODUCTION") == "1"
        self.snap = midtransclient.Snap(
            is_production=self.is_production,
            server_key=self.server_key,
            client_key=self.client_key
        )

    def create_checkout(self, subscription: Any, amount: float, currency: str, return_url: str) -> Checkout:
        param = {
            "transaction_details": {
                "order_id": f"SUB-{subscription.id}-{int(os.times()[4])}",
                "gross_amount": int(amount)
            },
            "customer_details": {
                "first_name": subscription.company_name,
                "email": subscription.email
            },
            "callbacks": {
                "finish": return_url
            }
        }
        transaction = self.snap.create_transaction(param)
        return Checkout(id=transaction["token"], url=transaction["redirect_url"])

    def verify_webhook(self, headers: Dict[str, str], raw_body: bytes) -> WebhookEvent:
        import json
        notification = json.loads(raw_body)
        
        # Verify signature
        order_id = notification.get("order_id")
        status_code = notification.get("status_code")
        gross_amount = notification.get("gross_amount")
        signature_key = notification.get("signature_key")
        
        server_key = self.server_key or os.getenv("MIDTRANS_SERVER_KEY")
        if not server_key:
            raise ValueError("MIDTRANS_SERVER_KEY not set")

        # sha512(order_id + status_code + gross_amount + server_key)
        payload = f"{order_id}{status_code}{gross_amount}{server_key}"
        expected_signature = hashlib.sha512(payload.encode()).hexdigest()
        
        if signature_key != expected_signature:
            raise ValueError("Midtrans signature verification failed")

        status = "pending"
        transaction_status = notification.get("transaction_status")
        if transaction_status in ["capture", "settlement"]:
            status = "succeeded"
        elif transaction_status in ["deny", "expire", "cancel"]:
            status = "failed"

        # Parse sub_id from order_id: SUB-{sub_id}-{ts}
        subscription_id = None
        if order_id and order_id.startswith("SUB-"):
            parts = order_id.split("-")
            if len(parts) >= 2:
                subscription_id = parts[1]

        return WebhookEvent(
            event_type=transaction_status,
            payment_id=notification.get("transaction_id"),
            status=status,
            raw_data=notification,
            subscription_id=int(subscription_id) if subscription_id else None,
            amount=float(gross_amount) if gross_amount else None,
            currency=notification.get("currency", "IDR").upper()
        )

    def refund(self, payment_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        return self.snap.api_client.refund(payment_id, {"amount": int(amount)} if amount else {})

    def list_methods(self, country: Optional[str] = None) -> List[Dict[str, Any]]:
        return [
            {"code": "bank_transfer", "label": "Bank Transfer (VA)", "icon": "Landmark"},
            {"code": "qris", "label": "QRIS", "icon": "QrCode"},
            {"code": "gopay", "label": "GoPay", "icon": "Wallet"},
            {"code": "shopeepay", "label": "ShopeePay", "icon": "Wallet"},
        ]
