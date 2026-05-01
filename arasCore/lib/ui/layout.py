# -*- coding: utf-8 -*-
"""
arasCore/lib/ui/layout.py — Single Source of Truth for Form Layout.

Flow:
  - layout_json in DB  → parse and render
  - layout_json empty  → generate default JSON → save to DB → parse and render

Default and saved layout always go through the same parse path.
"""
import json
import logging

logger = logging.getLogger(__name__)


def get_available_fields(tbl):
    return [c for c in tbl.columns if c.show_in_form]


def parse_layout(data: dict, field_map: dict, child_table_map: dict = None) -> list:
    """Maps a JSON section definition to WTForms fields / child table configs."""
    if not data or not isinstance(data, dict):
        return []

    sections = []
    child_table_map = child_table_map or {}

    for item in data.get("sections", []):
        if item.get("type") == "column_break":
            continue

        label  = item.get("label", "")
        width  = item.get("width", 12)
        fields = []

        for fitem in item.get("fields", []):
            fname  = fitem["name"] if isinstance(fitem, dict) else fitem
            fwidth = fitem.get("width", 12) if isinstance(fitem, dict) else 12

            field = field_map.get(fname.lower())
            if field:
                fields.append({"name": fname, "field": field, "width": fwidth, "type": "field"})
                continue

            ct_config = child_table_map.get(fname) or child_table_map.get(fname.lower())
            if ct_config:
                open_in_tab = fitem.get("open_in_tab", False) if isinstance(fitem, dict) else False
                ct_config["open_in_tab"] = open_in_tab
                fields.append({"name": fname, "ct": ct_config, "width": fwidth,
                                "type": "child_table", "open_in_tab": open_in_tab})
                ct_config["_is_placed"] = True
                continue

            logger.debug(f"[layout] '{fname}' not found in field_map or child_table_map")

        if fields or label:
            sections.append({"label": label, "width": width, "fields": fields})

    return sections


def _build_default_json(table_name, table_id, field_map, child_tables):
    """
    Build a serializable layout JSON dict for the default layout.
    This is saved to DB so default and saved layouts share the same parse path.
    """
    hidden = {'id', 'created_at', 'updated_at', 'deleted_at',
              'created_by_id', 'updated_by_id', 'is_active', 'csrf_token'}
    SUMMARY_TYPES = {'decimal', 'float', 'integer', 'currency'}
    SUMMARY_NAMES = {'total', 'subtotal', 'amount', 'balance', 'tax', 'discount',
                     'charge', 'paid', 'due'}

    def _is_summary(c):
        return c.field_type in SUMMARY_TYPES and any(kw in c.name.lower() for kw in SUMMARY_NAMES)

    info_fields    = []
    summary_fields = []

    if table_id:
        try:
            from arasCore.lib.core.extensions import db
            from arasCore.admin.models import AppManagerColumn
            cols = (db.session.query(AppManagerColumn)
                    .filter_by(table_id=table_id, show_in_form=True)
                    .order_by(AppManagerColumn.order).all())
            for c in cols:
                cname_low = c.name.lower()
                if cname_low in hidden:
                    continue
                entry = {"name": c.name, "width": 6, "type": "field"}
                if _is_summary(c):
                    summary_fields.append(entry)
                else:
                    info_fields.append(entry)
        except Exception as e:
            logger.warning(f"[layout] default JSON build failed for table {table_id}: {e}")

    if not info_fields and not summary_fields:
        # Fallback: use field_map keys directly
        info_fields = [{"name": f.name, "width": 6, "type": "field"}
                       for f in field_map.values() if f.name.lower() not in hidden]

    sections = []
    if info_fields:
        sections.append({"label": "Details", "width": 12, "fields": info_fields})

    for ct in (child_tables or []):
        ct_name = ct.get("model_name") or ct.get("title", "")
        sections.append({
            "label":  ct.get("title", ct_name),
            "width":  12,
            "fields": [{"name": ct_name, "width": 12, "type": "child_table", "open_in_tab": False}]
        })

    if summary_fields:
        sections.append({"label": "Summary", "width": 12, "fields": summary_fields})

    return [{"label": table_name, "sections": sections or
             [{"label": "Details", "width": 12, "fields": []}]}]


def _save_layout_to_db(table_id, layout_data):
    """Persist generated default layout to DB so it becomes the source of truth."""
    try:
        from arasCore.lib.core.extensions import db
        from arasCore.admin.models import AppManagerTable
        tbl = db.session.query(AppManagerTable).filter_by(id=table_id).first()
        if tbl and not tbl.layout_json:
            tbl.layout_json = json.dumps(layout_data)
            db.session.commit()
            logger.info(f"[layout] Default layout saved to DB for table_id={table_id}")
    except Exception as e:
        logger.warning(f"[layout] Could not save default layout to DB: {e}")


def _parse_layout_tabs(table_name, layout_json, form, table_id=None, child_tables=None) -> list:
    """
    Main layout engine. Always reads from / writes to layout_json in DB.
    Default layout is generated once, saved to DB, then parsed like any saved layout.
    """
    # Build field map
    field_map = {}
    for f in form:
        fname = f.name.lower()
        field_map[fname] = f
        if fname.endswith("_id"):
            field_map[fname.replace("_id", "")] = f
        else:
            field_map[fname + "_id"] = f

    # Build child table lookup map
    child_table_map = {}
    for ct in (child_tables or []):
        if "model_name" in ct:
            child_table_map[ct["model_name"].lower()] = ct
        if "title" in ct:
            child_table_map[ct["title"].lower()] = ct

    # Always read layout_json from DB so form and designer share the same source
    actual_json = None
    if table_id:
        try:
            from arasCore.admin.models import AppManagerTable
            from arasCore.lib.core.extensions import db
            tbl = db.session.query(AppManagerTable).filter_by(id=table_id).first()
            if tbl:
                actual_json = tbl.layout_json
        except Exception as e:
            logger.warning(f"[layout] DB read failed for table {table_id}: {e}")
            actual_json = layout_json  # fallback to snapshot on DB error
    if actual_json is None:
        actual_json = layout_json

    # Generate default if still empty, then save it
    if not actual_json:
        default_data = _build_default_json(table_name, table_id, field_map, child_tables)
        if table_id:
            _save_layout_to_db(table_id, default_data)
        data = default_data
    else:
        try:
            data = json.loads(actual_json) if isinstance(actual_json, str) else actual_json
            if not data:
                raise ValueError("empty")
        except Exception as e:
            logger.error(f"[layout] JSON parse failed for {table_name}: {e}")
            data = _build_default_json(table_name, table_id, field_map, child_tables)

    # Normalize single-tab (dict) to list
    if not isinstance(data, list):
        data = [{"label": table_name, "sections": data.get("sections", [])}]

    tabs = []
    for tdata in data:
        tabs.append({
            "label":    tdata.get("label", table_name),
            "sections": parse_layout(tdata, field_map, child_table_map=child_table_map)
        })

    return tabs or [{"label": table_name, "sections": []}]
