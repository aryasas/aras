from core import Aras
from .models import Party, Contact

class PartyView(Aras.View):
    model = Party
    title = "Parties"
    icon = "pi pi-users"

class ContactView(Aras.View):
    model = Contact
    title = "Contacts"
    icon = "pi pi-user"
