from core import Aras
from ..base.document import DOC_LAYOUT_HEADER, DOC_LAYOUT_NOTES
from .models import ItemCategory, Item, Location, StockMovement, PriceList, PromoBundle, \
    ItemUom, ItemBundle, ItemLocation, PromoBundleItem, StockMovementLine, DeliveryNote

class ItemCategoryView(Aras.View):
    model = ItemCategory
    title = "Item Categories"
    icon = "pi pi-tags"
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["name", "account_cogs_id", "account_stock_id", "account_variance_id", "account_revenue_id", "account_purchase_id"],
        },
    ]

class ItemView(Aras.View):
    model = Item
    title = "Items"
    icon = "pi pi-box"
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["name", "code", "sku", "category_id", "uom_id", "uom_purchase_id", "uom_sales_id", "is_active", "is_stock_item", "for_sales", "for_purchase"],
        },
        {"key": "stock", "title": "Stock", "fields": ["qty_on_hand", "stock_by_location"]},
        {"key": "alternate_units", "title": "Alternate Units", "fields": ["uoms"]},
        {"key": "prices", "title": "Prices", "fields": ["pricelists"]},
        {"key": "accounts", "title": "Accounts", "fields": ["accounts"]},
    ]

class ItemUomView(Aras.View):
    model = ItemUom
    title = "Item UOMs"
    standalone = True
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": [
                "uom_id",
                "factor"
            ],
        },
    ]

class ItemBundleView(Aras.View):
    model = ItemBundle
    title = "Item Bundle Components"
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["bundle_item_id", "component_item_id", "qty", "uom_id", {"field": "notes", "rows": 3}],
        },
    ]

class ItemLocationView(Aras.View):
    model = ItemLocation
    title = "Item Locations"
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["item_id", "location_id", "min_qty", "max_qty"],
        },
    ]

class PriceListView(Aras.View):
    model = PriceList
    title = "Price Rules"
    layout = [
        {"title": "General Info", "fields": ["price_type_id", "is_blanket", "min_qty", "is_active"]},
        {"title": "Target", "fields": ["product_id", "product_category_id", "uom_id"]},
        {"title": "Price / Discount", "fields": ["price", "discount_pct"]},
        {"title": "Validity", "fields": ["valid_from", "valid_to"]}
    ]

class PromoBundleView(Aras.View):
    model = PromoBundle
    title = "Promotion Bundles"
    layout = [
        {"title": "Bundle Config", "fields": ["price_type_id", "is_active"]},
        {"title": "Validity", "fields": ["valid_from", "valid_to"]},
        {"title": "Items", "fields": ["items"]}
    ]

class PromoBundleItemView(Aras.View):
    model = PromoBundleItem
    title = "Promo Items"

class LocationView(Aras.View):
    model = Location
    title = "Locations"
    icon = "pi pi-map-marker"
    layout = [
        {"title": "General", "fields": ["name", "location_type", "is_group", "parent_id"]}
    ]

class StockMovementView(Aras.View):
    model = StockMovement
    title = "Stock Movements"
    icon = "pi pi-sync"
    layout = [
        {"title": "Header", "fields": ["number", "doc_date", "status"]},
        {"title": "Route", "fields": ["from_location_id", "to_location_id"]},
        {"title": "Items", "fields": ["lines"]},
        DOC_LAYOUT_NOTES
    ]

class StockMovementLineView(Aras.View):
    model = StockMovementLine
    title = "Movement Lines"

class DeliveryNoteView(Aras.View):
    model = DeliveryNote
    title = "Delivery Notes"
    icon = "pi pi-truck"
    layout = [
        {"title": "Header", "fields": ["number", "party_id", "doc_date", "status"]},
        {"title": "Source", "fields": ["location_id"]},
        {"title": "Items", "fields": ["lines"]},
        DOC_LAYOUT_NOTES
    ]

