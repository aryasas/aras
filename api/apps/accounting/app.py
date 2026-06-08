from core import Aras
from . import views # Trigger view registration
from . import handlers as _handlers  # noqa: F401 — registers workflow handlers
from . import org_actions as _org_actions  # noqa: F401 — attaches mirror_coa to Organization
from .routers.print_router import router as print_router
from .routers.report_router import router as report_router
from .vocabulary_router import vocabulary_router
from .seeds.standard import seed_trade_defaults
from . import reports  # noqa: F401  # registers builtin reports with the engine

from core.logic.discovery import autodiscover_models
from .models import * # Import all models for discovery
from .config_models import AccountingConfig  # noqa: F401 — typed per-org config

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

class Accounting(Aras.App):
    app_name = "accounting"
    app_label = "Accounting"
    icon = "Calculator"
    saas_module = "accounting"

    config_sections = [
        ConfigSection(key="general", label="General", scope="module", fields=[
            ConfigField(key="enable_multi_currency", type="bool", default=False, label="Enable Multi-Currency"),
        ]),
        ConfigSection(key="posting", label="Posting", scope="module", fields=[
            ConfigField(key="enable_auto_journal", type="bool", default=True, label="Enable Auto-Journaling",
                        help="When off, workflow transitions skip the post_journal_entry handler. Useful for manual bookkeeping or staging environments."),
            ConfigField(key="auto_post_journals", type="bool", default=False, label="Auto-Post Journal Entries"),
            ConfigField(key="require_approval_above", type="number", default=0, label="Require Approval Above Amount", help="0 = no threshold"),
        ]),
        ConfigSection(key="matching", label="Matching", scope="module", fields=[
            ConfigField(key="match_qty_tolerance_pct", type="number", default=0, label="Quantity Tolerance %"),
            ConfigField(key="match_price_tolerance_pct", type="number", default=0, label="Price Tolerance %"),
        ]),
    ]

    routers = [print_router, accounting_api_router, vocabulary_router, report_router]
    seeds = [seed_trade_defaults]

    config_model = AccountingConfig
    jobs = [
        {
            "key": "overdue-ar-digest",
            "schedule_cron": "0 8 * * *",
            "handler_path": "apps.accounting.notifications.send_overdue_ar_digest",
            "enabled_default": True,
        }
    ]

    models = autodiscover_models(__name__, [
        "models", "config_models", "org_presets"
    ])

    menu_groups = [
        {
            "label": "General Ledger",
            "icon": "Book",
            "models": ["accounting_accounts", "accounting_entries", "accounting_fiscal_periods", "accounting_tax_rates"]
        },
        {
            "label": "Inflow",
            "icon": "ArrowDownLeft",
            "models": ["accounting_inflow_invoices"]
        },
        {
            "label": "Outflow",
            "icon": "ArrowUpRight",
            "models": ["accounting_purchase_orders", "accounting_outflow_invoices", "accounting_grns"]
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

    # claude-sonnet-4-6
    @classmethod
    def register_services(cls):
        from core.service_registry import ServiceRegistry
        from .services.journal import JournalService
        from .services.payment import PaymentService
        from .services.org_defaults import acc_default, stock_default
        from .models import InflowInvoice, InflowInvoiceLine, Account, OutflowInvoice, OutflowInvoiceLine
        ServiceRegistry.register("JournalService", JournalService)
        ServiceRegistry.register("PaymentService", PaymentService)
        ServiceRegistry.register("InflowInvoice", InflowInvoice)
        ServiceRegistry.register("InflowInvoiceLine", InflowInvoiceLine)
        ServiceRegistry.register("OutflowInvoice", OutflowInvoice)
        ServiceRegistry.register("OutflowInvoiceLine", OutflowInvoiceLine)
        ServiceRegistry.register("Account", Account)
        ServiceRegistry.register("acc_default", acc_default)
        ServiceRegistry.register("acc_stock_default", stock_default)

    @classmethod
    def seed(cls, db):
        from .seed_coa import seed_coa
        # Use first org for COA seed if available
        from core.workspace.models import Organization
        org = db.query(Organization).first()
        if org:
            seed_coa(db, org.id)
