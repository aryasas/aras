from core import Aras
from .models import PotSession, PotTerminal

class PotTerminalView(Aras.View):
    model = PotTerminal
    title = "POT Terminals"
    icon = "Monitor"
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
    icon = "Clock"
    layout = [
        {"key": "header", "title": "Header", "fields": ["number", "terminal_id", "mode", "status", "doc_date", "opening_balance", "closing_balance"]},
        {"key": "summary", "title": "Summary", "fields": ["total_sales", "total_purchase", "invoice_count"]},
        {"key": "sales_invoices", "type": "linked_list", "title": "Sales Invoices", "resource": "accounting/inflow-invoices", "fk_field": "pos_session_id"},
        {"key": "purchase_invoices", "type": "linked_list", "title": "Purchase Invoices", "resource": "accounting/outflow-invoices", "fk_field": "pos_session_id"},
    ]

