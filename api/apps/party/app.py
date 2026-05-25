from core import Aras
from core.logic.discovery import autodiscover_models
from . import views  # noqa: F401

class Party(Aras.App):
    app_name = "party"
    table_prefix = "erp_party"
    app_label = "Parties"
    icon = "Contact"
    models = autodiscover_models(__name__, ["models"])
