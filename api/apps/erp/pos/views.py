from core import Aras
from .models import PosSession, PosOrder, PosOrderLine

class PosSessionView(Aras.View):
    model = PosSession
    title = "POS Sessions"
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

class PosOrderView(Aras.View):
    model = PosOrder
    title = "POS Orders"
    layout = [
        {
            "title": "General",
            "fields": ["number", "doc_date", "status", "customer_id", "pricelist_id"]
        },
        {
            "title": "Items",
            "fields": ["lines"]
        }
    ]

class PosOrderLineView(Aras.View):
    model = PosOrderLine
    title = "POS Order Lines"
