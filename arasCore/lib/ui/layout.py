# -*- coding: utf-8 -*-
"""
arasCore/lib/layout.py — The Single Source of Truth for Form Arrangement.

This module resolves the visual arrangement of fields, sections, and tabs.
It handles two distinct states:
1. DEFAULT: Used when no custom layout has been saved in the Form Designer.
2. OVERRIDE: Used when a custom JSON layout exists in the database.

CRITICAL SYNC: This logic MUST align with the Form Designer (React) to ensure 
that "Architecture" view in Designer matches the initial Form view.
"""
import json
import logging

logger = logging.getLogger(__name__)

def get_available_fields(tbl):
    """
    Utility to filter columns from AppManagerColumn that are eligible for form display.
    Used by internal processes and potentially the Designer's initial bootstrap.
    """
    return [c for c in tbl.columns if c.show_in_form]

def parse_layout(data: dict, field_map: dict, child_table_map: dict = None) -> list:
    """
    Recursively maps a JSON section definition to actual WTForms field instances
    or Child Table configurations.
    """
    if not data or not isinstance(data, dict):
        return []

    sections = []
    raw_sections = data.get("sections", [])
    child_table_map = child_table_map or {}
    
    for item in raw_sections:
        if item.get("type") == "column_break":
            continue
            
        label  = item.get("label", "")
        width  = item.get("width", 12)
        fields = []
        
        for fitem in item.get("fields", []):
            fname = fitem["name"] if isinstance(fitem, dict) else fitem
            fwidth = fitem.get("width", 12) if isinstance(fitem, dict) else 12
            
            # 1. Check if it's a standard WTForms field
            target_field = field_map.get(fname.lower())
            if target_field:
                fields.append({
                    "name":  fname,
                    "field": target_field,
                    "width": fwidth,
                    "type":  "field"
                })
                continue

            # 2. Check if it's a Child Table (match by model_name or title)
            # Try exact match first, then lowercase match
            ct_config = child_table_map.get(fname) or child_table_map.get(fname.lower())
            if ct_config:
                fields.append({
                    "name":  fname,
                    "ct":    ct_config,
                    "width": fwidth,
                    "type":  "child_table"
                })
                # Mark as placed so it doesn't appear in auto-tabs
                ct_config["_is_placed"] = True
                continue

            logger.debug(f"[layout] element '{fname}' not found in field_map or child_table_map")
        
        if fields or label:
            sections.append({
                "label": label, 
                "width": width, 
                "fields": fields
            })

    return sections

def _parse_layout_tabs(table_name, layout_json, form, table_id=None, child_tables=None) -> list:
    """
    The main engine for rendering form layouts. 
    Now supports interleaving Child Tables via child_tables list.
    """
    
    # 1. Build a resilient field map from the WTForms instance
    field_map = {}
    for f in form:
        fname = f.name.lower()
        field_map[fname] = f
        if fname.endswith("_id"):
            field_map[fname.replace("_id", "")] = f
        else:
            field_map[fname + "_id"] = f

    # 2. Build child table map for easy lookup during parsing
    child_table_map = {}
    if child_tables:
        for ct in child_tables:
            # allow matching by model_name (e.g. "acc_sales_invoice_line") 
            # or by title (e.g. "Lines")
            if "model_name" in ct:
                child_table_map[ct["model_name"].lower()] = ct
            if "title" in ct:
                child_table_map[ct["title"].lower()] = ct
    
    def generate_default_layout():
        """
        INTERNAL DEFAULT ENGINE: Called when layout_json is empty.
        Aligns the initial Form view with the Designer's 'Architecture' list.
        """
        # System fields that should NEVER appear in any form by default
        hidden = {
            'id', 'created_at', 'updated_at', 'deleted_at', 
            'created_by_id', 'updated_by_id', 'is_active', 'csrf_token'
        }
        
        default_fields = []
        
        # LOGIC: Prioritize Database Metadata (AppManagerColumn)
        # This is where Form Designer gets its field list.
        if table_id:
            try:
                from arasCore.lib.core.extensions import db
                from arasCore.admin.models import AppManagerColumn
                # Fetch only fields marked for form, following the DB order
                cols = (db.session.query(AppManagerColumn)
                        .filter_by(table_id=table_id, show_in_form=True)
                        .order_by(AppManagerColumn.order).all())
                
                for c in cols:
                    cname_low = c.name.lower()
                    if cname_low in field_map and cname_low not in hidden:
                        default_fields.append({
                            "name": c.name, 
                            "field": field_map[cname_low], 
                            "width": 6
                        })
            except Exception as e:
                logger.warning(f"[layout] DB-driven default failed for table {table_id}: {e}")

        # FALLBACK: If DB columns are missing, use Model Introspection
        if not default_fields:
            default_fields = [
                {"name": f.name, "field": f, "width": 6} 
                for f in form if f.name.lower() not in hidden
            ]

        # Return as a single 'Details' tab
        return [{
            "label":    table_name,
            "sections": [{
                "label": "Details",
                "width": 12,
                "fields": default_fields
            }]
        }]

    # --- EXECUTION FLOW ---
    
    # CASE: No saved layout -> Generate Default
    if not layout_json:
        return generate_default_layout()

    try:
        # CASE: Existing layout -> Parse JSON
        data = json.loads(layout_json) if isinstance(layout_json, str) else layout_json
        if not data:
            return generate_default_layout()
    except Exception as e:
        logger.error(f"[layout] JSON parse failed for {table_name}: {e}")
        return generate_default_layout()

    # Normalize single-section layouts into tabbed format
    if not isinstance(data, list):
        data = [{"label": table_name, "width": 12, "sections": data.get("sections", [])}]
    
    tabs = []
    for tdata in data:
        parsed_sections = parse_layout(tdata, field_map, child_table_map=child_table_map)
        tabs.append({
            "label":    tdata.get("label", table_name),
            "sections": parsed_sections
        })
    
    return tabs if tabs else generate_default_layout()
