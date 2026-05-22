from ..app import ERP
from . import views # Trigger view registration

from core.logic.discovery import autodiscover_models
from .models import * # Import all models for discovery
from .services import posting as _posting  # noqa: F401 — registers on_transition callbacks
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.lib.database import get_db
from core.response import ok

stock_extra_router = APIRouter()

@stock_extra_router.get("/items/{item_id}/stock")
def get_item_stock(item_id: int, db: Session = Depends(get_db)):
    from .services.stock import StockComputeService
    return ok({
        "total": StockComputeService.compute_qty(db, item_id),
        "by_location": StockComputeService.compute_qty_by_location(db, item_id),
    })

class Stock(ERP):
    app_name = "erp_stock"
    app_type = "module"
    app_label = "Stock"
    icon = "Package"

    models = autodiscover_models(__name__, ["models"])
    routers = [stock_extra_router]

    menu_groups = [
        {
            "label": "Master Data",
            "icon": "Database",
            "models": ["erp_stock_products", "erp_stock_categories", "erp_stock_locations"]
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

