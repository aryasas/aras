from core import Aras
from . import models

class Party(Aras.App):
    app_name = "party"
    table_prefix = "erp_party"
    app_label = "Parties"
    icon = "Contact"
    models = [models.Party, models.Contact]
