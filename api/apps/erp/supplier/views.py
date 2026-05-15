from core import Aras
from .models import Supplier

class SupplierView(Aras.View):
    model = Supplier
    title = "Suppliers"
    layout = [
        {
            "title": "General Information",
            "fields": ["name", "code", "tax_id"]
        },
        {
            "title": "Contact Details",
            "fields": ["email", "phone", "mobile", "address"]
        }
    ]
