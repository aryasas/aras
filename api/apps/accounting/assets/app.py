from core import Aras
from core.registry.master_data_registry import MasterEntity
from . import models as assets_models

class Asset(Aras.App):
    app_name = "accounting.assets"
    app_label = "Fixed Assets"
    parent_name = "accounting"
    app_type = "module"
    icon = "Building2"
    requires = ["accounting"]
    optional_features = {
        "enable_asset_depreciation_journal": "accounting",
    }
    models = [assets_models.AssetCategory, assets_models.Asset]
    
    master_data = [
        MasterEntity(key="asset_category", model=assets_models.AssetCategory, scope="module", icon="FolderTree", order=10),
    ]
