from typing import Iterable, Optional

from sqlalchemy import Column, String, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship

from ..base.model import Model


# claude-opus-4-8
TRADE_APP_NAMES = frozenset({"accounting", "stock", "party", "pot", "report"})

# claude-opus-4-8
# Org profiles that do NOT buy/sell: they never get the trade (Sales/Receivables/
# Stock) default dashboard even if trade apps are installed platform-wide. Denylist,
# not allowlist — any new/unknown profile defaults to trade so a normal business
# gets the money dashboard out of the box. Profile keys mirror apps.accounting.profiles
# (kept here as plain strings; core must not import apps). "general" is intentionally
# NOT here: an unconfigured org with trade apps installed still gets the trade dashboard.
NON_TRADE_PROFILES = frozenset({"npo", "school", "library", "hospital", "government"})


# claude-opus-4-8
GENERIC_WIDGET_DEFINITIONS = (
    {
        "name": "total_users",
        "title": "Total Users",
        "widget_type": "stat",
        "resource_name": "core_users",
        "config_json": {"icon": "Users", "color": "indigo"},
        "size": "col-span-1",
        "order": 1,
    },
    {
        "name": "recent_activity",
        "title": "Recent Activity",
        "widget_type": "list",
        "resource_name": "core_activity_logs",
        "config_json": {"limit": 5},
        "size": "col-span-2",
        "order": 2,
    },
    {
        "name": "active_apps",
        "title": "Installed Apps",
        "widget_type": "stat",
        "resource_name": "core_apps",
        "config_json": {"icon": "Package", "color": "emerald"},
        "size": "col-span-1",
        "order": 3,
    },
    {
        "name": "total_products",
        "title": "Total Products",
        "widget_type": "stat",
        "resource_name": "stock_items",
        "config_json": {"icon": "Package", "color": "indigo"},
        "size": "col-span-1",
        "order": 4,
    },
    {
        "name": "recent_movements",
        "title": "Recent Stock Movements",
        "widget_type": "list",
        "resource_name": "stock_movements",
        "config_json": {"limit": 5},
        "size": "col-span-2",
        "order": 5,
    },
    {
        "name": "total_accounts",
        "title": "Total Accounts",
        "widget_type": "stat",
        "resource_name": "accounting_accounts",
        "config_json": {"icon": "Calculator", "color": "emerald"},
        "size": "col-span-1",
        "order": 6,
    },
    {
        "name": "recent_entries",
        "title": "Recent Journal Entries",
        "widget_type": "list",
        "resource_name": "accounting_entries",
        "config_json": {"limit": 5},
        "size": "col-span-2",
        "order": 7,
    },
    {
        "name": "total_customers",
        "title": "Total Customers",
        "widget_type": "stat",
        "resource_name": "party_parties",
        "config_json": {"icon": "Users", "color": "indigo"},
        "size": "col-span-1",
        "order": 8,
    },
)


# claude-opus-4-8
TRADE_WIDGET_DEFINITIONS = (
    {
        "name": "trade_today_sales",
        "title": "Today's Sales",
        "widget_type": "trade_kpi",
        "resource_name": "report/dashboard",
        "config_json": {"metric": "today_sales", "title_key": "trx_in", "link": "/accounting/inflow-invoices"},
        "size": "col-span-1",
        "order": 101,
    },
    {
        "name": "trade_month_profit",
        "title": "This Month Profit",
        "widget_type": "trade_kpi",
        "resource_name": "report/dashboard",
        "config_json": {"metric": "month_profit", "link": "/reports"},
        "size": "col-span-1",
        "order": 102,
    },
    {
        "name": "trade_receivables_total",
        "title": "Owed by Customers",
        "widget_type": "trade_kpi",
        "resource_name": "report/dashboard",
        "config_json": {"metric": "receivables_total", "title_key": "party", "link": "/reports"},
        "size": "col-span-1",
        "order": 103,
    },
    {
        "name": "trade_low_stock_count",
        "title": "Low Stock Items",
        "widget_type": "trade_kpi",
        "resource_name": "report/dashboard",
        "config_json": {"metric": "low_stock_count", "link": "/stock/items"},
        "size": "col-span-1",
        "order": 104,
    },
    {
        "name": "trade_low_stock_items",
        "title": "Low Stock Watchlist",
        "widget_type": "trade_list",
        "resource_name": "report/dashboard",
        "config_json": {"source": "low_stock_items", "link": "/stock/items"},
        "size": "col-span-2",
        "order": 105,
    },
    {
        "name": "trade_recent_documents",
        "title": "Recent Documents",
        "widget_type": "trade_list",
        "resource_name": "report/dashboard",
        "config_json": {"source": "recent_documents", "link": "/reports"},
        "size": "col-span-2",
        "order": 106,
    },
)


class WidgetModel(Model):
    """
    Registry for Dashboard Widgets.
    Widgets can be Stats, Charts, or Recent Activity lists.
    """
    __tablename__ = "core_widgets"
    __hidden__ = True

    name = Column(String(100), nullable=False)
    title = Column(String(100), nullable=False)
    widget_type = Column(String(50), nullable=False) # stat, chart, list
    resource_name = Column(String(100), nullable=True) # Data source
    config_json = Column(JSON, nullable=True) # Options like color, icon, query filters
    size = Column(String(20), default="col-span-1") # UI layout hint
    order = Column(Integer, default=0)
    
    # Optional: Link to a specific App
    app_id = Column(Integer, ForeignKey("core_apps.id", ondelete="CASCADE"), nullable=True)
    app = relationship("AppModel", backref="widgets")

    @classmethod
    # claude-opus-4-8
    def _report_app_id(cls, db) -> Optional[int]:
        from .app_model import AppModel

        report_app = db.query(AppModel).filter(
            AppModel.name == "report",
            AppModel.is_active == True,
        ).first()
        return report_app.id if report_app else None

    @classmethod
    # claude-opus-4-8
    def _defs_with_report_app(cls, db, definitions: Iterable[dict]) -> list[dict]:
        report_app_id = cls._report_app_id(db)
        output: list[dict] = []
        for definition in definitions:
            row = dict(definition)
            if row["name"].startswith("trade_"):
                row["app_id"] = report_app_id
            output.append(row)
        return output

    @classmethod
    # claude-opus-4-8
    def seed_defaults(cls, db) -> None:
        definitions = cls._defs_with_report_app(db, [*GENERIC_WIDGET_DEFINITIONS, *TRADE_WIDGET_DEFINITIONS])
        updatable_fields = ("title", "widget_type", "resource_name", "config_json", "size", "order", "app_id")

        for definition in definitions:
            row = db.query(cls).filter(cls.name == definition["name"]).first()
            if not row:
                db.add(cls(**definition))
                continue
            for field in updatable_fields:
                if getattr(row, field) != definition.get(field):
                    setattr(row, field, definition.get(field))
        db.flush()

    @classmethod
    # claude-opus-4-8
    def _get_installed_app_names(cls, db) -> set[str]:
        from .app_model import AppModel

        return {
            name for (name,) in db.query(AppModel.name).filter(AppModel.is_active == True).all()
            if name
        }

    @classmethod
    # claude-opus-4-8
    def is_trade_org(
        cls,
        db,
        org_id: Optional[int] = None,
        installed_app_names: Optional[Iterable[str]] = None,
    ) -> bool:
        # Per-org gate: a non-trading profile (NGO/school/etc.) is never a trade org,
        # even where trade apps are installed globally. Otherwise require the trade apps.
        if org_id is not None:
            from core.workspace.models import Organization

            org = db.get(Organization, org_id)
            if org is not None and (org.profile or "general") in NON_TRADE_PROFILES:
                return False
        app_names = set(installed_app_names) if installed_app_names is not None else cls._get_installed_app_names(db)
        return TRADE_APP_NAMES.issubset(app_names)

    @classmethod
    # claude-opus-4-8
    def _default_widget_names(
        cls,
        db,
        org_id: Optional[int] = None,
        installed_app_names: Optional[Iterable[str]] = None,
    ) -> list[str]:
        definitions = TRADE_WIDGET_DEFINITIONS if cls.is_trade_org(db, org_id, installed_app_names) else GENERIC_WIDGET_DEFINITIONS
        return [definition["name"] for definition in definitions]

    @classmethod
    # claude-opus-4-8
    def get_default_widgets(
        cls,
        db,
        org_id: Optional[int] = None,
        installed_app_names: Optional[Iterable[str]] = None,
    ):
        names = cls._default_widget_names(db, org_id, installed_app_names)
        widgets = db.query(cls).filter(cls.name.in_(names)).all()
        by_name = {widget.name: widget for widget in widgets}
        return [by_name[name] for name in names if name in by_name]

    @classmethod
    # claude-opus-4-8
    def get_default_widget_payloads(
        cls,
        db,
        org_id: Optional[int] = None,
        installed_app_names: Optional[Iterable[str]] = None,
    ) -> list[dict]:
        from core.logic.discovery import resolve_resource_path

        payloads: list[dict] = []
        for widget in cls.get_default_widgets(db, org_id, installed_app_names):
            data = widget.to_dict()
            data["resource_path"] = resolve_resource_path(widget.resource_name) or widget.resource_name
            payloads.append(data)
        return payloads
