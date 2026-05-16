from core import Aras
from .models import ProductCategory, Product, Location, StockMovement, PriceList, PromoBundle, \
    ProductUom, PromoBundleItem, StockMovementLine, DeliveryNote

class ProductCategoryView(Aras.View):
    model = ProductCategory
    title = "Product Categories"
    icon = "pi pi-tags"
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["name", "account_sale_id", "account_purchase_id", "account_cogs_id", "account_stock_id", "account_variance_id"],
        },
    ]

class ProductView(Aras.View):
    model = Product
    title = "Products"
    icon = "pi pi-box"
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["name", "sku", "category_id", "uom_id", "is_active"],
        },
        {
            "key": "pricing",
            "title": "Pricing",
            "fields": ["price", "pricelist_id", "currency_id"],
        },
        {
            "key": "accounting",
            "title": "Accounting",
            "fields": ["account_stock_id", "account_cogs_id", "account_variance_id"],
        },
        {
            "key": "notes",
            "title": "Notes",
            "fields": ["description"],
        },
        {"key": "alternate_units", "title": "Alternate Units", "fields": ["uoms"]},
        {"key": "prices", "title": "Prices", "fields": ["pricelists"]},
    ]

class ProductUomView(Aras.View):
    model = ProductUom
    title = "Product Units"
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["name", "ratio", "uom_id"],
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
        {"title": "General", "fields": ["name", "code", "location_type", "is_group", "parent_id"]}
    ]

class StockMovementView(Aras.View):
    model = StockMovement
    title = "Stock Movements"
    icon = "pi pi-sync"
    layout = [
        {"title": "Header", "fields": ["number", "doc_date", "status"]},
        {"title": "Route", "fields": ["from_location_id", "to_location_id"]},
        {"title": "Items", "fields": ["lines"]},
        {"title": "Notes", "fields": ["notes"]}
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
        {"title": "Notes", "fields": ["notes"]}
    ]

