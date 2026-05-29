# claude-opus-4-7
from sqlalchemy import String, Integer, Boolean, DateTime, Date, Numeric, Enum as SQLEnum
from ..registry import register_handler

@register_handler("lookup")
def handle_lookup(column):
    if column.foreign_keys:
        return "lookup", None
    return None

@register_handler("select")
def handle_select(column):
    choices = column.info.get("choices")
    if choices:
        return "select", [{"label": str(c), "value": c} for c in choices]
    
    col_type = column.type
    if isinstance(col_type, SQLEnum) or hasattr(col_type, "enums"):
        return "select", [{"label": str(e), "value": str(e)} for e in getattr(col_type, "enums", [])]
    return None

@register_handler("file_image")
def handle_file_image(column):
    if isinstance(column.type, String):
        if any(suffix in column.name for suffix in ["_file", "_path", "_attachment"]):
            return "file", None
        if any(suffix in column.name for suffix in ["_image", "_photo", "_avatar"]):
            return "image", None
    return None

@register_handler("scalar")
def handle_scalar(column):
    col_type = column.type
    if isinstance(col_type, (Integer, Numeric)):
        return "number", None
    if isinstance(col_type, Boolean):
        return "boolean", None
    if isinstance(col_type, DateTime):
        return "datetime", None
    if isinstance(col_type, Date):
        return "date", None
    if isinstance(col_type, String):
        return "string", None
    return None
