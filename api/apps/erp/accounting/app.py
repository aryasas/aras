from ..app import ERP
from .models import Account, JournalEntry, JournalEntryLine, SalesInvoice, SalesInvoiceLine, \
    PurchaseInvoice, PurchaseInvoiceLine, SalesOrder, SalesOrderLine, SalesOrderCharge, \
    PurchaseOrder, PurchaseOrderLine, PurchaseOrderCharge, SalesInvoiceCharge, PurchaseInvoiceCharge, \
    Payment, PaymentAllocation, FiscalPeriod
from . import views # Trigger view registration

class Accounting(ERP):
    app_name = "erp_accounting"
    app_label = "Accounting"
    icon = "Calculator"

    models = [
        Account, FiscalPeriod,
        JournalEntry, JournalEntryLine, 
        SalesOrder, SalesOrderLine, SalesOrderCharge,
        SalesInvoice, SalesInvoiceLine, SalesInvoiceCharge,
        PurchaseOrder, PurchaseOrderLine, PurchaseOrderCharge,
        PurchaseInvoice, PurchaseInvoiceLine, PurchaseInvoiceCharge,
        Payment, PaymentAllocation
    ]

    menu_groups = [
        {
            "label": "General Ledger",
            "icon": "Book",
            "models": ["erp_accounting_accounts", "erp_accounting_entries", "erp_accounting_fiscal_periods"]
        },
        {
            "label": "Sales",
            "icon": "ArrowUpRight",
            "models": ["erp_accounting_sales_orders", "erp_accounting_sales_invoices"]
        },
        {
            "label": "Purchase",
            "icon": "ArrowDownLeft",
            "models": ["erp_accounting_purchase_orders", "erp_accounting_purchase_invoices"]
        },
        {
            "label": "Payments",
            "icon": "CreditCard",
            "models": ["erp_accounting_payments"]
        }
    ]
