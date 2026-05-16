from core import Aras
from ..app import ERP
from . import models

class PartyApp(Aras.App):
    app_name = "party"
    parent_name = "erp"
    app_label = "Parties"
    models = [models.Party, models.Contact]
