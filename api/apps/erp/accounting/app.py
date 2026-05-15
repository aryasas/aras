from core import Aras
from .models import Account, JournalEntry, JournalEntryLine, SalesInvoice, SalesInvoiceLine, \
    PurchaseInvoice, PurchaseInvoiceLine
from . import views # Trigger view registration

class AccountingApp(Aras.App):
    app_name = "erp_accounting"
    parent_name = "erp"
    app_label = "Accounting"
    icon = "Calculator"
    
    models = [Account, JournalEntry, JournalEntryLine, SalesInvoice, SalesInvoiceLine, \
              PurchaseInvoice, PurchaseInvoiceLine]
    
    menu_groups = [
        {
            "label": "Master Data",
            "icon": "Database",
            "models": ["erp_accounting_accounts"]
        },
        {
            "label": "Transactions",
            "icon": "ShoppingCart",
            "models": ["erp_accounting_sales_invoices", "erp_accounting_purchase_invoices", "erp_accounting_entries"]
        }
    ]
