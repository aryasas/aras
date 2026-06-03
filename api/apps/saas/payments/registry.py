# gemini-2-5-flash
import logging
from typing import Dict, Optional, List
from core import Aras
from .base import PaymentProvider

class PaymentProviderRegistry(Aras):
    _providers: Dict[str, PaymentProvider] = {}

    @classmethod
    def register(cls, provider: PaymentProvider):
        cls._providers[provider.code] = provider
        logging.info(f"Registered payment provider: {provider.code}")

    @classmethod
    def get(cls, code: str) -> Optional[PaymentProvider]:
        return cls._providers.get(code)

    @classmethod
    def choose_for_country(cls, country: Optional[str]) -> PaymentProvider:
        if country == "ID":
            midtrans = cls.get("midtrans")
            if midtrans: return midtrans
            xendit = cls.get("xendit")
            if xendit: return xendit
            
        # Default to Stripe for international or fallback
        stripe = cls.get("stripe")
        if stripe:
            return stripe
            
        if cls._providers:
            return next(iter(cls._providers.values()))
            
        raise ValueError("No payment providers registered")

    @classmethod
    def list_all(cls) -> List[PaymentProvider]:
        return list(cls._providers.values())

    @classmethod
    def handle_webhook_success(cls, db, provider_code, event):
        from ..models import SaaSPayment, SaaSInvoice, Subscription
        from datetime import datetime, timezone
        # 1. Update/Create Payment
        payment = db.query(SaaSPayment).filter_by(provider_payment_id=event.payment_id, provider_code=provider_code).first()
        if not payment:
            if event.subscription_id:
                payment = SaaSPayment(
                    subscription_id=event.subscription_id,
                    provider_code=provider_code,
                    provider_payment_id=event.payment_id,
                    amount=event.amount or 0,
                    currency=event.currency or "USD",
                    status="succeeded"
                )
                db.add(payment)
        else:
            payment.status = "succeeded"
            
        db.commit()
        
        if payment:
            # 2. Mark Invoice paid
            invoice = db.query(SaaSInvoice).filter_by(subscription_id=payment.subscription_id, status="unpaid").first()
            if invoice:
                invoice.status = "paid"
                invoice.paid_at = datetime.now(timezone.utc)
                invoice.payment_id = payment.id
            
            # 3. Fire Subscription.approve if pending
            sub = db.query(Subscription).get(payment.subscription_id)
            if sub and sub.status in ["pending", "pending_payment"]:
                sub.approve(db)
            
            db.commit()
