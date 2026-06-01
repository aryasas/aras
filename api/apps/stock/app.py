from core import Aras
from . import views # Trigger view registration

from core.logic.discovery import autodiscover_models
from .models import * # Import all models for discovery
from .services import posting as _posting  # noqa: F401 — registers on_transition callbacks
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.lib.database import get_db
from core.response import ok

from core.auth.service import get_current_user

stock_extra_router = APIRouter()

@stock_extra_router.get("/items/{item_id}/stock")
def get_item_stock(item_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    from .services.stock import StockComputeService
    return ok({
        "total": StockComputeService.compute_qty(db, item_id),
        "by_location": StockComputeService.compute_qty_by_location(db, item_id),
    })

from core.registry.config_registry import ConfigSection, ConfigField
class Stock(Aras.App):
    app_name = "stock"
    app_label = "Stock"
    icon = "Package"
    saas_module = "stock"
    requires = ["accounting"]

    optional_features = {
        "enable_perpetual_inventory": "accounting",
        "enable_auto_journal": "accounting",
    }

    config_sections = [
        ConfigSection(key="general", label="General", scope="module", fields=[
            ConfigField(key="valuation_method", type="choice", default="fifo", label="Valuation Method",
                        choices=[("fifo", "FIFO"), ("lifo", "LIFO"), ("average", "Weighted Average")]),
            ConfigField(key="default_warehouse", type="string", label="Default Warehouse Code"),
            ConfigField(key="allow_negative_stock", type="bool", default=False, label="Allow Negative Stock"),
            ConfigField(key="auto_create_serial", type="bool", default=False, label="Auto-Generate Serial Numbers"),
        ]),
        ConfigSection(key="reorder", label="Reorder", scope="module", fields=[
            ConfigField(key="enable_reorder_alerts", type="bool", default=True, label="Enable Reorder Alerts"),
            ConfigField(key="default_lead_time_days", type="number", default=7, label="Default Lead Time (days)"),
        ]),
    ]

    models = autodiscover_models(__name__, ["models"])
    routers = [stock_extra_router]

    menu_groups = [
        {
            "label": "Master Data",
            "icon": "Database",
            "models": ["stock_items", "stock_categories", "stock_locations"]
        },
        {
            "label": "Operations",
            "icon": "Truck",
            "models": ["stock_delivery_notes", "stock_movements"]
        },
        {
            "label": "Pricing & Promo",
            "icon": "Tag",
            "models": ["stock_pricelists", "stock_promo_bundles"]
        }
    ]

