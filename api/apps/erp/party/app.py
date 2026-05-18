from ..app import ERP
from . import models

class Party(ERP):
    app_name = "erp_party"
    app_type = "module"
    app_label = "Parties"
    icon = "Contact"
    models = [models.Party, models.Contact]
