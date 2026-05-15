from core import Aras
from .models import Customer, Contact

class CustomerView(Aras.View):
    model = Customer
    title = "Customers"
    layout = [
        {
            "title": "General Information",
            "fields": ["name", "code", "tax_id"]
        },
        {
            "title": "Contact Details",
            "fields": ["email", "phone", "mobile", "address"]
        },
        {
            "title": "Settings",
            "fields": ["pricelist_id"]
        },
        {
            "title": "Contacts",
            "fields": ["contacts"]
        }
    ]

class ContactView(Aras.View):
    model = Contact
    title = "Customer Contacts"
