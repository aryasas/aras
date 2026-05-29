# gemini-2-5-flash
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from core.lib.database import get_db
from core.response import ok, err
from ..models import Subscription, SaaSPayment, SaaSInvoice
from ..payments.registry import PaymentProviderRegistry
import logging

router = APIRouter(prefix="/payments", tags=["SaaS Payments"])

@router.post("/checkout")
async def create_checkout(payload: dict, db: Session = Depends(get_db), request: Request = None):
    subscription_id = payload.get("subscription_id")
    return_url = payload.get("return_url")
    
    if not subscription_id or not return_url:
        return err("subscription_id and return_url are required")
        
    subscription = db.query(Subscription).get(subscription_id)
    if not subscription:
        return err("Subscription not found")
        
    # Get plan to find amount
    if not subscription.plan:
        return err("Subscription has no plan")
        
    amount = subscription.plan.price
    currency = subscription.plan.currency
    
    # Choose provider (Batch 2 will add geo logic)
    geo_country = getattr(request.state, "geo_country", None)
    try:
        provider = PaymentProviderRegistry.choose_for_country(geo_country)
    except ValueError as e:
        return err(str(e))
        
    try:
        checkout = provider.create_checkout(subscription, amount, currency, return_url)
        return ok({"checkout_url": checkout.url, "checkout_id": checkout.id})
    except Exception as e:
        logging.error(f"Checkout creation failed: {str(e)}")
        return err(f"Checkout failed: {str(e)}")

@router.post("/webhook/{provider_code}")
async def payment_webhook(provider_code: str, request: Request, db: Session = Depends(get_db)):
    provider = PaymentProviderRegistry.get(provider_code)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
        
    raw_body = await request.body()
    headers = dict(request.headers)
    
    try:
        event = provider.verify_webhook(headers, raw_body)
    except ValueError as e:
        logging.warning(f"Webhook verification failed for {provider_code}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    # Handle event
    if event.status == "succeeded":
        PaymentProviderRegistry.handle_webhook_success(db, provider_code, event)
        logging.info(f"Payment succeeded for {provider_code}: {event.payment_id}")
        
    return {"status": "ok"}

@router.get("/methods")
async def list_payment_methods(request: Request):
    geo_country = getattr(request.state, "geo_country", None)
    # Return methods for all registered providers (Batch 1 simplified)
    methods = []
    for provider in PaymentProviderRegistry.list_all():
        methods.extend(provider.list_methods(geo_country))
    return ok(methods)
