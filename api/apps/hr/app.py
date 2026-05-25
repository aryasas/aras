from core import Aras
from core.logic.discovery import autodiscover_models
from . import views  # noqa: F401

class HR(Aras.App):
    app_name = "hr"
    table_prefix = "erp_hr"
    app_label = "Human Resources"
    icon = "Users"
    models = autodiscover_models(__name__, ["models"])
