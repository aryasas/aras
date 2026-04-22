# -*- coding: utf-8 -*-
"""
arasCore/lib/layout.py
=======================
Parses AppManagerTable.layout_json and returns a structured layout descriptor
that the form template can render as Bootstrap tabs / sections / column breaks.

Layout JSON format (list of dicts):
  [
    {"type": "tab", "label": "General", "fields": ["name", "status", ...]},
    {"type": "tab", "label": "Details", "sections": [
        {"type": "section", "label": "Address", "fields": ["street", "city"]},
        {"type": "column_break"},
        {"type": "section", "label": "Contact",  "fields": ["phone", "email"]}
    ]},
  ]

Simplified flat form (no tab/section nesting):
  [{"type": "section", "label": "Info", "fields": ["name", "email"]}]

If layout_json is None/empty the helper returns None and the template falls
back to the flat base_form_fields.html render.
"""
import json
import logging

logger = logging.getLogger(__name__)


def parse_layout(tbl, form):
    """
    Returns a list of tab dicts suitable for template rendering, or None if no
    layout is defined.

    Each tab dict:
      {"label": str, "sections": [
          {"label": str, "fields": [(field_name, field_obj), ...]},
          ...  (column_break inserts a new column within a row)
      ]}
    """
    raw = getattr(tbl, "layout_json", None)
    if not raw:
        return None

    try:
        layout = json.loads(raw) if isinstance(raw, str) else raw
    except (ValueError, TypeError):
        logger.warning(f"[layout] Invalid layout_json for table {tbl.name}")
        return None

    if not isinstance(layout, list) or not layout:
        return None

    # Build field lookup from form
    field_map = {f.name: f for f in form if f.type not in ("HiddenField", "CSRFTokenField")}

    # Normalise: if top-level items are sections/fields (no tabs), wrap in one tab
    first = layout[0]
    if first.get("type") in ("section", "column_break") or "fields" in first:
        layout = [{"type": "tab", "label": "", "content": layout}]

    tabs = []
    for item in layout:
        if item.get("type") != "tab":
            continue
        tab_label    = item.get("label", "")
        raw_content  = item.get("sections") or item.get("content") or []
        # Also accept flat "fields" on the tab
        if "fields" in item and not raw_content:
            raw_content = [{"type": "section", "label": "", "fields": item["fields"]}]

        sections = _parse_sections(raw_content, field_map)
        tabs.append({"label": tab_label, "sections": sections})

    return tabs or None


def _parse_sections(raw_content, field_map):
    """Turn raw section/column_break list into column groups."""
    current_row   = []   # list of section dicts in current column
    columns       = [current_row]

    for item in raw_content:
        t = item.get("type", "section")
        if t == "column_break":
            current_row = []
            columns.append(current_row)
        else:
            label  = item.get("label", "")
            fields = [
                (name, field_map[name])
                for name in item.get("fields", [])
                if name in field_map
            ]
            if fields:
                current_row.append({"label": label, "fields": fields})

    # Remove empty columns
    columns = [c for c in columns if c]
    return columns
