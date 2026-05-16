from ..app import ERP
from ..app import ERP
from .models import Account, JournalEntry, JournalEntryLine, InflowInvoice, InflowInvoiceLine, \
    OutflowInvoice, OutflowInvoiceLine, InflowOrder, InflowOrderLine, InflowOrderCharge, \
    OutflowOrder, OutflowOrderLine, OutflowOrderCharge, InflowInvoiceCharge, OutflowInvoiceCharge, \
    Payment, PaymentAllocation, FiscalPeriod
from . import views # Trigger view registration

class Accounting(ERP):
    app_name = "erp_accounting"
    app_label = "Accounting"
    icon = "Calculator"

    models = [
        Account, FiscalPeriod,
        JournalEntry, JournalEntryLine, 
        InflowOrder, InflowOrderLine, InflowOrderCharge,
        InflowInvoice, InflowInvoiceLine, InflowInvoiceCharge,
        OutflowOrder, OutflowOrderLine, OutflowOrderCharge,
        OutflowInvoice, OutflowInvoiceLine, OutflowInvoiceCharge,
        Payment, PaymentAllocation
    ]

    menu_groups = [
        {
            "label": "General Ledger",
            "icon": "Book",
            "models": ["erp_accounting_accounts", "erp_accounting_entries", "erp_accounting_fiscal_periods"]
        },
        {
            "label": "Inflow",
            "icon": "ArrowUpRight",
            "models": ["erp_accounting_inflow_orders", "erp_accounting_inflow_invoices"]
        },
        {
            "label": "Outflow",
            "icon": "ArrowDownLeft",
            "models": ["erp_accounting_outflow_orders", "erp_accounting_outflow_invoices"]
        },
        {
            "label": "Payments",
            "icon": "CreditCard",
            "models": ["erp_accounting_payments"]
        }
    ]
