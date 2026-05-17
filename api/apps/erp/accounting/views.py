from core import Aras
from core.response import ok, err
from ..base.document import DOC_LAYOUT_HEADER, DOC_LAYOUT_NOTES
from .models import Account, JournalEntry, InflowInvoice, OutflowInvoice, Payment, FiscalPeriod

class AccountView(Aras.View):
    model = Account
    icon = "pi pi-list"
    fields = {
        "is_group": {"title": "Is Group Account", "ui_type": "boolean"},
        "account_type": {"title": "Type"}
    }
    layout = [
        {
            "key": "account",
            "title": "Account",
            "fields": ["name", "code", "account_type", "currency_id"],
        },
        {
            "key": "opening",
            "title": "Opening",
            "fields": ["opening_balance", "is_active"],
        },
    ]

class FiscalPeriodView(Aras.View):
    model = FiscalPeriod
    title = "Fiscal Periods"
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["name", "start_date", "end_date", "status"],
        },
    ]

class InflowInvoiceView(Aras.View):
    model = InflowInvoice
    title = "Inflow Invoices"
    icon = "pi pi-file"
    layout = [
        {"title": "Header", "fields": ["number", "party_id", "doc_date", "doc_type", "pricelist_id", "status", "currency_id"]},
        {"title": "Items", "fields": ["lines"]},
        {"title": "Taxes & Charges", "fields": ["charges"]},
        {"title": "Financials", "fields": ["subtotal", "total_charge", "total_amount"]},
        DOC_LAYOUT_NOTES
    ]

class OutflowInvoiceView(Aras.View):
    model = OutflowInvoice
    title = "Outflow Invoices"
    icon = "pi pi-file-pdf"
    layout = [
        {"title": "Header", "fields": ["number", "supplier_id", "doc_date", "doc_type", "pricelist_id", "status", "currency_id"]},
        {"title": "Items", "fields": ["lines"]},
        {"title": "Taxes & Charges", "fields": ["charges"]},
        {"title": "Financials", "fields": ["subtotal", "total_charge", "total_amount"]},
        DOC_LAYOUT_NOTES
    ]

class PaymentView(Aras.View):
    model = Payment
    icon = "pi pi-wallet"
    layout = [
        {"title": "Header", "fields": ["number", "currency_id", "payment_type", "party_type", "party_id", "doc_date", "status"]},
        {"title": "Payment Details", "fields": ["account_id", "mode_of_payment_id", "amount", "reference"]},
        {"title": "Allocations", "fields": ["allocations"]},
        DOC_LAYOUT_NOTES # Replaced Notes section
    ]

