from core import Aras
from . import views # Trigger view registration
from . import handlers as _handlers  # noqa: F401 — registers workflow handlers
from .routers.print_router import router as print_router

from core.logic.discovery import autodiscover_models
from .models import * # Import all models for discovery

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.lib.database import get_db
from core.logic.permissions import check_permissions
from core.auth.service import user_can_access_org

accounting_api_router = APIRouter()

@accounting_api_router.get("/payments/{payment_id}/open_invoices")
def get_open_invoices_for_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    user: object = Depends(check_permissions("accounting_payments", "READ")),
):
    from .models import Payment
    from .services.payment import PaymentService

    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.org_id and not user_can_access_org(db, user, payment.org_id):
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

from core.registry.config_registry import ConfigSection, ConfigField
from core.registry.master_data_registry import MasterEntity
from .models import Account, FiscalPeriod

class Accounting(Aras.App):
    app_name = "accounting"
    app_label = "Accounting"
    icon = "Calculator"
    saas_module = "accounting"

    master_data = [
        MasterEntity(key="account", model=Account, scope="module", icon="ListTree", order=10),
        MasterEntity(key="fiscal_period", model=FiscalPeriod, scope="module", icon="CalendarDays", order=20),
    ]

    config_sections = [
        ConfigSection(key="general", label="General", scope="module", fields=[
            ConfigField(key="fiscal_year_start_month", type="number", default=1, label="Fiscal Year Start Month", help="1=Jan, 12=Dec"),
            ConfigField(key="default_currency", type="string", default="USD", label="Default Currency", help="ISO 4217 code"),
            ConfigField(key="rounding_precision", type="number", default=2, label="Rounding Precision (decimals)"),
            ConfigField(key="enable_multi_currency", type="bool", default=False, label="Enable Multi-Currency"),
        ]),
        ConfigSection(key="posting", label="Posting", scope="module", fields=[
            ConfigField(key="enable_auto_journal", type="bool", default=True, label="Enable Auto-Journaling",
                        help="When off, workflow transitions skip the post_journal_entry handler. Useful for manual bookkeeping or staging environments."),
            ConfigField(key="auto_post_journals", type="bool", default=False, label="Auto-Post Journal Entries"),
            ConfigField(key="require_approval_above", type="number", default=0, label="Require Approval Above Amount", help="0 = no threshold"),
        ]),
    ]

    routers = [print_router, accounting_api_router]

    models = autodiscover_models(__name__, [
        "models"
    ])

    menu_groups = [
        {
            "label": "General Ledger",
            "icon": "Book",
            "models": ["accounting_accounts", "accounting_entries", "accounting_fiscal_periods"]
        },
        {
            "label": "Inflow",
            "icon": "ArrowDownLeft",
            "models": ["accounting_inflow_invoices"]
        },
        {
            "label": "Outflow",
            "icon": "ArrowUpRight",
            "models": ["accounting_outflow_invoices", "accounting_grns"]
        },
        {
            "label": "Payments",
            "icon": "CreditCard",
            "models": ["accounting_payments"]
        },
        {
            "label": "Fixed Assets",
            "icon": "Building2",
            "models": ["accounting_assets_assets", "accounting_assets_categories"]
        }
    ]

    @classmethod
    def seed(cls, db):
        from .seed_coa import seed_coa
        # Use first org for COA seed if available
        from apps.config.models import Organization
        org = db.query(Organization).first()
        if org:
            seed_coa(db, org.id)
