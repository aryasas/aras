from core import Aras
from .models import AssetCategory, Asset

class AssetCategoryView(Aras.View):
    model = AssetCategory
    title = "Asset Categories"
    icon = "pi pi-tags"
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["name", "depreciation_method", "useful_life_years"],
        },
    ]

class AssetView(Aras.View):
    model = Asset
    title = "Assets"
    icon = "pi pi-box"
    layout = [
        {
            "key": "asset_info",
            "title": "Asset Info",
            "fields": ["name", "category_id", "serial_number", "location", "status"],
        },
        {
            "key": "valuation",
            "title": "Valuation",
            "fields": ["purchase_date", "purchase_value", "current_value"],
        },
    ]
