from ..app import ERP
from . import models

class Asset(ERP):
    app_name = "erp_asset"
    app_type = "module"
    app_label = "Fixed Assets"
    icon = "Package"
    models = [models.AssetCategory, models.Asset]
