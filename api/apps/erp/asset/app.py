from core import Aras
from ..app import ERP
from . import models

class AssetApp(Aras.App):
    app_name = "asset"
    parent_name = "erp"
    app_label = "Fixed Assets"
    models = [models.AssetCategory, models.Asset]
