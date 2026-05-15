from core import Aras
from .models import Account, JournalEntry, JournalEntryLine, SalesInvoice, SalesInvoiceLine, \
    PurchaseInvoice, PurchaseInvoiceLine

class AccountView(Aras.View):
    model = Account
    title = "Accounts"

class JournalEntryView(Aras.View):
    model = JournalEntry
    title = "Journal Entries"
    layout = [
        {
            "title": "General",
            "fields": ["number", "doc_date", "status", "reference"]
        },
        {
            "title": "Lines",
            "fields": ["lines"]
        },
        {
            "title": "Notes",
            "fields": ["notes"]
        }
    ]

class JournalEntryLineView(Aras.View):
    model = JournalEntryLine
    title = "Entry Lines"

class SalesInvoiceView(Aras.View):
    model = SalesInvoice
    title = "Sales Invoices"
    layout = [
        {
            "title": "General",
            "fields": ["number", "doc_date", "status", "customer_id", "currency_id", "pricelist_id"]
        },
        {
            "title": "Totals",
            "fields": ["subtotal", "total_tax", "total_amount"]
        },
        {
            "title": "Items",
            "fields": ["lines"]
        }
    ]

class SalesInvoiceLineView(Aras.View):
    model = SalesInvoiceLine
    title = "Invoice Lines"

class PurchaseInvoiceView(Aras.View):
    model = PurchaseInvoice
    title = "Purchase Invoices"
    layout = [
        {
            "title": "General",
            "fields": ["number", "doc_date", "status", "supplier_id", "currency_id"]
        },
        {
            "title": "Totals",
            "fields": ["subtotal", "total_tax", "total_amount"]
        },
        {
            "title": "Items",
            "fields": ["lines"]
        }
    ]

class PurchaseInvoiceLineView(Aras.View):
    model = PurchaseInvoiceLine
    title = "Purchase Invoice Lines"
