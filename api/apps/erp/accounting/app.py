from ..app import ERP
from ..app import ERP
from .models import Account, JournalEntry, JournalEntryLine, InflowInvoice, InflowInvoiceLine, \
    OutflowInvoice, OutflowInvoiceLine, InflowOrder, InflowOrderLine, InflowOrderCharge, \
    OutflowOrder, OutflowOrderLine, OutflowOrderCharge, InflowInvoiceCharge, OutflowInvoiceCharge, \
    Payment, PaymentAllocation, FiscalPeriod, GoodsReceiptNote
from .models_grn import GoodsReceiptLine
from . import views # Trigger view registration
from .routers.print_router import router as print_router

class Accounting(ERP):
    app_name = "erp_accounting"
    app_label = "Accounting"
    icon = "Calculator"

    routers = [print_router]

    models = [
        Account, FiscalPeriod,
        JournalEntry, JournalEntryLine, 
        InflowOrder, InflowOrderLine, InflowOrderCharge,
        InflowInvoice, InflowInvoiceLine, InflowInvoiceCharge,
        OutflowOrder, OutflowOrderLine, OutflowOrderCharge,
        OutflowInvoice, OutflowInvoiceLine, OutflowInvoiceCharge,
        Payment, PaymentAllocation,
        GoodsReceiptNote, GoodsReceiptLine
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
            "models": ["erp_accounting_outflow_orders", "erp_accounting_outflow_invoices", "erp_accounting_grns"]
        },
        {
            "label": "Payments",
            "icon": "CreditCard",
            "models": ["erp_accounting_payments"]
        }
    ]
