from core import Aras
from .models import PotSession, PotOrder, PotOrderLine, PotTerminal

class PotTerminalView(Aras.View):
    model = PotTerminal
    title = "POT Terminals"
    icon = "pi pi-desktop"
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["name", "location_id", "is_active", "receipt_header", "receipt_footer"],
        },
    ]

class PotSessionView(Aras.View):
    model = PotSession
    title = "POT Sessions"
    icon = "pi pi-clock"
    layout = [
        {"key": "header", "title": "Header", "fields": ["number", "terminal_id", "mode", "status", "doc_date", "opening_balance", "closing_balance"]},
        {"key": "summary", "title": "Summary", "fields": ["total_sales", "total_purchase", "invoice_count"]},
        {"type": "linked_list", "title": "Sales Invoices", "resource": "erp/accounting/outflow-invoices", "fk_field": "pos_session_id"},
        {"type": "linked_list", "title": "Purchase Invoices", "resource": "erp/accounting/inflow-invoices", "fk_field": "pos_session_id"},
    ]

class PotOrderView(Aras.View):
    model = PotOrder
    title = "POT Orders"
    layout = [
        {
            "key": "header",
            "title": "Header",
            "fields": ["number", "doc_date", "status", "party_id", "pricelist_id"],
        },
        {
            "key": "items",
            "title": "Items",
            "fields": ["lines"],
        },
    ]

class PotOrderLineView(Aras.View):
    model = PotOrderLine
    title = "POT Order Lines"
