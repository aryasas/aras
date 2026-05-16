from core import Aras
from .models import AssetCategory, Asset

class AssetCategoryView(Aras.View):
    model = AssetCategory
    title = "Asset Categories"
    icon = "pi pi-tags"

class AssetView(Aras.View):
    model = Asset
    title = "Assets"
    icon = "pi pi-box"
