from core import Aras
from .models import PotSession, PotOrder, PotOrderLine, PotTerminal

class PotTerminalView(Aras.View):
    model = PotTerminal
    title = "POT Terminals"
    icon = "pi pi-desktop"

class PotSessionView(Aras.View):
    model = PotSession
    title = "POT Sessions"
    icon = "pi pi-clock"
    layout = [
        {
            "title": "General",
            "fields": ["number", "doc_date", "status", "opening_balance", "closing_balance"]
        },
        {
            "title": "Orders",
            "fields": ["orders"]
        }
    ]

class PotOrderView(Aras.View):
    model = PotOrder
    title = "POT Orders"
    layout = [
        {
            "title": "General",
            "fields": ["number", "doc_date", "status", "party_id", "pricelist_id"]
        },
        {
            "title": "Items",
            "fields": ["lines"]
        }
    ]

class PotOrderLineView(Aras.View):
    model = PotOrderLine
    title = "POT Order Lines"
