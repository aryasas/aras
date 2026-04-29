# -*- coding: utf-8 -*-
"""
arasCore/lib/widget_registry.py
Built-in widget renderers for the dashboard builder.

Three built-in widget types:
  CountWidget — total row count for a model/table
  SumWidget   — sum of a numeric column
  ChartWidget — grouped count or sum, returns labels+data for Chart.js

Custom widget types can be registered via register_widget().
"""
import logging
from typing import Callable

logger = logging.getLogger(__name__)

_widget_handlers: dict[str, Callable] = {}


def register_widget(widget_type: str, handler: Callable) -> None:
    _widget_handlers[widget_type] = handler


def resolve_widget(widget: "AppManagerDashboard") -> dict:
    """
    Compute a widget's data payload. Returns a dict with at least 'value' or 'labels'+'data'.
    Called by the dashboard route at render time.
    """
    wtype = widget.widget_type or "count"
    handler = _widget_handlers.get(wtype)
    if handler:
        try:
            return handler(widget)
        except Exception as e:
            logger.warning(f"[widget] {wtype} error for '{widget.name}': {e}")
            return {"error": str(e)}
    return {"error": f"Unknown widget type: {wtype}"}


# ── Built-in: CountWidget ─────────────────────────────────────────────────────

def _count_handler(widget) -> dict:
    import json
    from arasCore.lib.core.extensions import db
    cfg = json.loads(widget.config_json or "{}")
    table_name = widget.data_source  # sqlalchemy table name
    filter_col = cfg.get("filter_col")
    filter_val = cfg.get("filter_val")
    sql = f"SELECT COUNT(*) FROM `{table_name}`"
    if filter_col and filter_val is not None:
        sql += f" WHERE `{filter_col}` = :val"
        count = db.session.execute(
            db.text(sql), {"val": filter_val}
        ).scalar()
    else:
        count = db.session.execute(db.text(sql)).scalar()
    return {"value": count or 0, "label": widget.label}


# ── Built-in: SumWidget ───────────────────────────────────────────────────────

def _sum_handler(widget) -> dict:
    import json
    from arasCore.lib.core.extensions import db
    cfg = json.loads(widget.config_json or "{}")
    table_name = widget.data_source
    sum_col = cfg.get("sum_col", "id")
    filter_col = cfg.get("filter_col")
    filter_val = cfg.get("filter_val")
    sql = f"SELECT COALESCE(SUM(`{sum_col}`), 0) FROM `{table_name}`"
    if filter_col and filter_val is not None:
        sql += f" WHERE `{filter_col}` = :val"
        total = db.session.execute(db.text(sql), {"val": filter_val}).scalar()
    else:
        total = db.session.execute(db.text(sql)).scalar()
    return {"value": float(total or 0), "label": widget.label}


# ── Built-in: ChartWidget ─────────────────────────────────────────────────────

def _chart_handler(widget) -> dict:
    import json
    from arasCore.lib.core.extensions import db
    cfg = json.loads(widget.config_json or "{}")
    table_name = widget.data_source
    group_col = cfg.get("group_col", "created_at")
    agg = cfg.get("agg", "count")           # count | sum
    agg_col = cfg.get("agg_col", "id")
    limit = int(cfg.get("limit", 7))
    if agg == "sum":
        sql = (f"SELECT `{group_col}`, COALESCE(SUM(`{agg_col}`), 0) "
               f"FROM `{table_name}` GROUP BY `{group_col}` "
               f"ORDER BY `{group_col}` DESC LIMIT :lim")
    else:
        sql = (f"SELECT `{group_col}`, COUNT(*) "
               f"FROM `{table_name}` GROUP BY `{group_col}` "
               f"ORDER BY `{group_col}` DESC LIMIT :lim")
    rows = db.session.execute(db.text(sql), {"lim": limit}).fetchall()
    labels = [str(r[0]) for r in reversed(rows)]
    data   = [float(r[1]) for r in reversed(rows)]
    return {"labels": labels, "data": data, "label": widget.label}


# Register built-ins
register_widget("count", _count_handler)
register_widget("sum",   _sum_handler)
register_widget("chart", _chart_handler)
