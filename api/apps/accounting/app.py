from core import Aras
from . import views # Trigger view registration
from . import handlers as _handlers  # noqa: F401 — registers workflow handlers
from .routers.print_router import router as print_router

from core.logic.discovery import autodiscover_models
from .models import * # Import all models for discovery

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.lib.database import get_db

accounting_api_router = APIRouter()

@accounting_api_router.get("/payments/{payment_id}/open_invoices")
def get_open_invoices_for_payment(payment_id: int, db: Session = Depends(get_db)):
    from .models import Payment
    from .services.payment import PaymentService

    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.payment_type not in ("Incoming", "Outgoing"):
        return []
    if payment.party_id is None:
        return []

    invoices = PaymentService.get_unpaid_invoices(db, payment.party_type, payment.party_id, payment.org_id)
    
    result = []
    for inv in invoices:
        result.append({
            "id": inv.id,
            "number": inv.number,
            "total_amount": inv.total_amount,
            "amount_due": inv.amount_due,
            "doc_date": inv.doc_date.isoformat() if inv.doc_date else None,
        })
    return result

class Accounting(Aras.App):
    app_name = "accounting"
    table_prefix = "erp_accounting"
    app_label = "Accounting"
    icon = "Calculator"

    routers = [print_router, accounting_api_router]

    models = autodiscover_models(__name__, [
        "models"
    ])

    menu_groups = [
        {
            "label": "General Ledger",
            "icon": "Book",
            "models": ["erp_accounting_accounts", "erp_accounting_entries", "erp_accounting_fiscal_periods"]
        },
        {
            "label": "Inflow",
            "icon": "ArrowDownLeft",
            "models": ["erp_accounting_inflow_invoices"]
        },
        {
            "label": "Outflow",
            "icon": "ArrowUpRight",
            "models": ["erp_accounting_outflow_invoices", "erp_accounting_grns"]
        },
        {
            "label": "Payments",
            "icon": "CreditCard",
            "models": ["erp_accounting_payments"]
        }
    ]
