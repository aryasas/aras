from core import Aras
from .models import ProductCategory, Product, Warehouse, StockMovement, StockMovementLine, \
    ProductUom, PriceList, PromoBundle, PromoBundleItem
from . import views # Trigger view registration

class StockApp(Aras.App):
    app_name = "erp_stock"
    parent_name = "erp"
    app_label = "Stock & Inventory"
    icon = "Package"
    
    models = [
        ProductCategory, Product, Warehouse, StockMovement, StockMovementLine,
        ProductUom, PriceList, PromoBundle, PromoBundleItem
    ]
    
    menu_groups = [
        {
            "label": "Master Data",
            "icon": "Database",
            "models": ["erp_stock_products", "erp_stock_categories", "erp_stock_warehouses", "erp_stock_product_uoms"]
        },
        {
            "label": "Pricing & Promos",
            "icon": "Tag",
            "models": ["erp_stock_pricelists", "erp_stock_promo_bundles"]
        },
        {
            "label": "Movements",
            "icon": "Truck",
            "models": ["erp_stock_movements"]
        }
    ]
