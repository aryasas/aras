from core import Aras
from core.logic.discovery import autodiscover_models
from . import views  # noqa: F401
from .seeds.standard import seed_trade_parties

class Party(Aras.App):
    app_name = "party"
    app_label = "Parties"
    icon = "Contact"
    models = autodiscover_models(__name__, ["models"])
    seeds = [seed_trade_parties]
