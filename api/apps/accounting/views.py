from core import Aras
from core.response import ok, err
from apps.base.document import DOC_LAYOUT_HEADER, DOC_LAYOUT_NOTES
from .models import Account, JournalEntry, JournalEntryLine, InflowInvoice, OutflowInvoice, Payment, FiscalPeriod

class AccountView(Aras.View):
    model = Account
    icon = "List"
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

class JournalEntryView(Aras.View):
    model = JournalEntry
    icon = "Book"
    layout = [
        {"title": "Header", "fields": ["number", "doc_date", "status", "currency_id", "source_type", "source_id"]},
        {"title": "Lines", "fields": ["lines"]},
        DOC_LAYOUT_NOTES
    ]

class JournalEntryLineView(Aras.View):
    model = JournalEntryLine
    fields = {
        "account_id": {"label": "Account"},
        "debit": {"label": "Debit"},
        "credit": {"label": "Credit"},
        "description": {"label": "Description"},
    }

class InflowInvoiceView(Aras.View):
    model = InflowInvoice
    title = "Inflow Invoices"
    icon = "FileText"
    layout = [
        {"title": "Header", "fields": ["number", "party_id", "doc_date", "doc_type", "pricelist_id", "status", "currency_id"]},
        {"title": "Items", "fields": ["lines"]},
        {"title": "Taxes & Charges", "fields": ["charges"]},
        {"title": "Financials", "tabs": [
            {"title": "Financials", "fields": ["subtotal", "total_charge", "total_amount"]},
            {"title": "Payments", "fields": ["amount_paid", "amount_due", "payment_allocations"]},
            {"title": "Journal Entries", "fields": ["journal_entries"]},
        ]},
        DOC_LAYOUT_NOTES
    ]

class OutflowInvoiceView(Aras.View):
    model = OutflowInvoice
    title = "Outflow Invoices"
    icon = "FileDigit"
    layout = [
        {"title": "Header", "fields": ["number", "party_id", "doc_date", "doc_type", "pricelist_id", "status", "currency_id"]},
        {"title": "Items", "fields": ["lines"]},
        {"title": "Taxes & Charges", "fields": ["charges"]},
        {"title": "Financials", "tabs": [
            {"title": "Financials", "fields": ["subtotal", "total_charge", "total_amount"]},
            {"title": "Payments", "fields": ["amount_paid", "amount_due", "payment_allocations"]},
            {"title": "Journal Entries", "fields": ["journal_entries"]},
        ]},
        DOC_LAYOUT_NOTES
    ]

class PaymentView(Aras.View):
    model = Payment
    icon = "Wallet"
    fields = {
        "allocations.invoice_type": {"read_only": True},
        "allocations.invoice_id": {"ui_type": "async_select", "choices_url": "/api/v1/accounting/payments/{parent_id}/open_invoices", "display_field": "number"},
    }
    layout = [
        {"title": "Header", "fields": ["number", "currency_id", "payment_type", "party_type", "party_id", "doc_date", "status"]},
        {"title": "Payment Details", "fields": ["account_id", "mode_of_payment_id", "amount", "reference"]},
        {"title": "Allocations", "fields": ["amount_allocated", "amount_unallocated", "allocations"], "actions": ["get_open_invoices", "auto_allocate"]},
        DOC_LAYOUT_NOTES
    ]
