from core import Aras
from . import models

class Asset(Aras.App):
    app_name = "asset"
    table_prefix = "erp_asset"
    app_label = "Fixed Assets"
    icon = "Package"
    requires = ["accounting"]
    optional_features = {
        "enable_asset_depreciation_journal": "accounting",
    }
    models = [models.AssetCategory, models.Asset]
