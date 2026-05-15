from ..app import ERP
from .models import ProductCategory, Product, Warehouse, Location, StockMovement, StockMovementLine, \
    ProductUom, PriceList, PromoBundle, PromoBundleItem, DeliveryNote, DeliveryNoteLine
from . import views # Trigger view registration

class Stock(ERP):
    app_name = "erp_stock"
    app_label = "Stock"
    icon = "Package"

    models = [
        ProductCategory, Product, Warehouse, Location, StockMovement, StockMovementLine,
        ProductUom, PriceList, PromoBundle, PromoBundleItem, DeliveryNote, DeliveryNoteLine
    ]

    menu_groups = [
        {
            "label": "Master Data",
            "icon": "Database",
            "models": ["erp_stock_products", "erp_stock_categories", "erp_stock_warehouses", "erp_stock_locations"]
        },
        {
            "label": "Operations",
            "icon": "Truck",
            "models": ["erp_stock_delivery_notes", "erp_stock_movements"]
        },
        {
            "label": "Pricing & Promo",
            "icon": "Tag",
            "models": ["erp_stock_pricelists", "erp_stock_promo_bundles"]
        }
    ]

