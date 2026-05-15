from core import Aras
from .models import ProductCategory, Product, Warehouse, StockMovement, PriceList, PromoBundle, \
    ProductUom, PromoBundleItem, StockMovementLine, DeliveryNote

class ProductCategoryView(Aras.View):
    model = ProductCategory
    title = "Product Categories"
    icon = "pi pi-tags"

class ProductView(Aras.View):
    model = Product
    title = "Products"
    icon = "pi pi-box"
    layout = [
        {"title": "General", "fields": ["name", "code", "category_id", "uom_id"]},
        {"title": "Alternate Units", "fields": ["uoms"]},
        {"title": "Prices", "fields": ["pricelists"]}
    ]

class ProductUomView(Aras.View):
    model = ProductUom
    title = "Product Units"

class PriceListView(Aras.View):
    model = PriceList
    title = "Price Rules"
    layout = [
        {"title": "General Info", "fields": ["price_type_id", "is_blanket", "min_qty"]},
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

class WarehouseView(Aras.View):
    model = Warehouse
    title = "Warehouses"
    icon = "pi pi-home"

class StockMovementView(Aras.View):
    model = StockMovement
    title = "Stock Movements"
    icon = "pi pi-sync"
    layout = [
        {"title": "Header", "fields": ["number", "doc_date", "status"]},
        {"title": "Route", "fields": ["from_warehouse_id", "to_warehouse_id"]},
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
        {"title": "Header", "fields": ["number", "customer_id", "doc_date", "status"]},
        {"title": "Source", "fields": ["warehouse_id"]},
        {"title": "Items", "fields": ["lines"]},
        {"title": "Notes", "fields": ["notes"]}
    ]

