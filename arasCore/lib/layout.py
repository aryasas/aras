# -*- coding: utf-8 -*-
"""
arasCore/lib/layout.py — The single source of truth for form arrangement.
"""
import json
import logging

logger = logging.getLogger(__name__)

def get_available_fields(tbl):
    """
    Returns the list of columns from mgr_column that should be in the form.
    """
    return [c for c in tbl.columns if c.show_in_form]

def parse_layout(data: dict, field_map: dict) -> list:
    """Parses a layout object into sections with fields mapped to WTForms field instances."""
    if not data or not isinstance(data, dict):
        return []

    sections = []
    raw_sections = data.get("sections", [])
    
    for item in raw_sections:
        if item.get("type") == "column_break":
            continue
            
        label  = item.get("label", "")
        width  = item.get("width", 12)
        fields = []
        
        for fitem in item.get("fields", []):
            fname = fitem["name"] if isinstance(fitem, dict) else fitem
            fwidth = fitem.get("width", 12) if isinstance(fitem, dict) else 12
            
            # Source of Truth mapping
            target_field = field_map.get(fname)
            if not target_field and not fname.endswith("_id"):
                target_field = field_map.get(f"{fname}_id")
            
            if target_field:
                fields.append({
                    "name":  fname,
                    "field": target_field,
                    "width": fwidth
                })
            else:
                logger.debug(f"[layout] field '{fname}' not found in form field_map")
        
        if fields or label:
            sections.append({
                "label": label, 
                "width": width, 
                "fields": fields
            })

    return sections

def _parse_layout_tabs(table_name, layout_json, form) -> list:
    """
    Central entry point for the real form renderer.
    """
    field_map = {f.name: f for f in form}

    default_tab = [{
        "label":    table_name,
        "sections": [{
            "label": "Details",
            "width": 12,
            "fields": [{"name": f.name, "field": f, "width": 6} for f in form if f.name not in ["id", "csrf_token"]]
        }]
    }]

    if not layout_json:
        return default_tab

    try:
        data = json.loads(layout_json) if isinstance(layout_json, str) else layout_json
        if not data:
            return default_tab
    except Exception as e:
        logger.error(f"[layout] Failed to parse JSON for {table_name}: {e}")
        return default_tab

    if not isinstance(data, list):
        data = [{"label": table_name, "width": 12, "sections": data.get("sections", [])}]
    
    tabs = []
    for tdata in data:
        parsed_sections = parse_layout(tdata, field_map)
        tabs.append({
            "label":    tdata.get("label", table_name),
            "sections": parsed_sections
        })
    
    return tabs if tabs else default_tab