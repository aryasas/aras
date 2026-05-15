from core import Aras
from .models import Account, JournalEntry, SalesInvoice, PurchaseInvoice, SalesOrder, \
    PurchaseOrder, Payment, FiscalPeriod

class AccountView(Aras.View):
    model = Account
    icon = "pi pi-list"
    fields = {
        "is_group": {"label": "Is Group Account", "ui_type": "boolean"},
        "account_type": {"label": "Type"}
    }

class FiscalPeriodView(Aras.View):
    model = FiscalPeriod
    title = "Fiscal Periods"

class SalesOrderView(Aras.View):
    model = SalesOrder
    title = "Sales Orders"
    icon = "pi pi-shopping-cart"
    layout = [
        {"title": "Header", "fields": ["number", "customer_id", "doc_date", "status"]},
        {"title": "Items", "fields": ["lines"]},
        {"title": "Taxes & Charges", "fields": ["charges"]},
        {"title": "Totals", "fields": ["subtotal", "total_charge", "total_amount"]},
        {"title": "Notes", "fields": ["notes"]}
    ]

class SalesInvoiceView(Aras.View):
    model = SalesInvoice
    title = "Sales Invoices"
    icon = "pi pi-file"
    layout = [
        {"title": "Header", "fields": ["number", "customer_id", "doc_date", "status", "currency_id"]},
        {"title": "Items", "fields": ["lines"]},
        {"title": "Taxes & Charges", "fields": ["charges"]},
        {"title": "Financials", "fields": ["subtotal", "total_charge", "total_amount"]},
        {"title": "Notes", "fields": ["notes"]}
    ]

class PurchaseOrderView(Aras.View):
    model = PurchaseOrder
    title = "Purchase Orders"
    icon = "pi pi-shopping-bag"
    layout = [
        {"title": "Header", "fields": ["number", "supplier_id", "doc_date", "status"]},
        {"title": "Items", "fields": ["lines"]},
        {"title": "Taxes & Charges", "fields": ["charges"]},
        {"title": "Totals", "fields": ["subtotal", "total_charge", "total_amount"]},
        {"title": "Notes", "fields": ["notes"]}
    ]

class PurchaseInvoiceView(Aras.View):
    model = PurchaseInvoice
    title = "Purchase Invoices"
    icon = "pi pi-file-pdf"
    layout = [
        {"title": "Header", "fields": ["number", "supplier_id", "doc_date", "status"]},
        {"title": "Items", "fields": ["lines"]},
        {"title": "Taxes & Charges", "fields": ["charges"]},
        {"title": "Financials", "fields": ["subtotal", "total_charge", "total_amount"]},
        {"title": "Notes", "fields": ["notes"]}
    ]

class PaymentView(Aras.View):
    model = Payment
    icon = "pi pi-wallet"
    layout = [
        {"title": "Header", "fields": ["number", "payment_type", "party_type", "party_id", "doc_date", "status"]},
        {"title": "Payment Details", "fields": ["account_id", "mode_of_payment_id", "amount", "reference"]},
        {"title": "Allocations", "fields": ["allocations"]},
        {"title": "Notes", "fields": ["notes"]}
    ]

