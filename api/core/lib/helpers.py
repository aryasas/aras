"""
Generic Helper Functions for Aras Framework.
"""
import re
import json
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

def to_snake_case(name: str) -> str:
    """Converts CamelCase to snake_case."""
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

def to_camel_case(snake_str: str) -> str:
    """Converts snake_case to CamelCase."""
    components = snake_str.split('_')
    return ''.join(x.title() for x in components)

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, Enum):
        return obj.value
    raise TypeError(f"Type {type(obj)} not serializable")

def format_currency(value: float, symbol: str = "$") -> str:
    """Formats a number as currency."""
    return f"{symbol}{value:,.2f}"

def slugify(text: str) -> str:
    """Simplifies text for use in URLs or identifiers."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text

def to_label_case(name: str) -> str:
    """Converts snake_case or technical names to human-readable labels."""
    if not name:
        return ""
    return name.replace("_", " ").title()
