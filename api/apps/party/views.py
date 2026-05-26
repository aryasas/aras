from core import Aras
from .models import Party, Contact

class PartyView(Aras.View):
    model = Party
    title = "Parties"
    icon = "Users"
    layout = [
        {
            "key": "identity",
            "title": "Identity",
            "fields": ["name", "role", "tax_id", "pricelist_id"],
        },
        {
            "key": "contact",
            "title": "Contact",
            "fields": ["email", "phone", "website"],
        },
        {
            "key": "address",
            "title": "Address",
            "fields": ["address", "city", "country"],
        },
    ]

class ContactView(Aras.View):
    model = Contact
    title = "Contacts"
    icon = "User"
    layout = [
        {
            "key": "info",
            "title": "Info",
            "fields": ["name", "designation", "is_primary"],
        },
        {
            "key": "contact",
            "title": "Contact",
            "fields": ["email", "phone"],
        },
    ]
