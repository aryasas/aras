# -*- coding: utf-8 -*-
"""
arasCore/lib/validator.py
Shared validation engine for dynamic app fields.

Reads validation rules from AppManagerColumn (required, min_value, max_value,
max_length, regex_pattern, unique) and returns a dict of field→error message.

Called by api_handler.py before create/update and by form rendering.
"""
import re
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _coerce(value: Any, field_type: str) -> Any:
    if value is None or value == "":
        return None
    try:
        if field_type in ("integer",):
            return int(value)
        if field_type in ("float", "decimal"):
            return float(value)
    except (TypeError, ValueError):
        pass
    return value


def validate_row(columns, data: dict, existing_obj=None) -> dict[str, str]:
    """
    Validate data dict against a list of AppManagerColumn objects.
    Returns {field_name: error_message} for each violation.
    `existing_obj` is passed for unique checks (to exclude the current row).
    """
    errors: dict[str, str] = {}

    for col in columns:
        name = col.name
        raw = data.get(name)
        value = _coerce(raw, getattr(col, "field_type", "string"))

        # required
        if getattr(col, "required", False) and (value is None or value == ""):
            errors[name] = f"{col.label} is required."
            continue

        if value is None or value == "":
            continue

        # max_length
        max_len = getattr(col, "max_length", None)
        if max_len and isinstance(value, str) and len(value) > max_len:
            errors[name] = f"{col.label} must not exceed {max_len} characters."
            continue

        # min / max (numeric and string length)
        min_val = getattr(col, "min_value", None)
        max_val = getattr(col, "max_value", None)
        if min_val is not None:
            try:
                if float(value) < float(min_val):
                    errors[name] = f"{col.label} must be ≥ {min_val}."
                    continue
            except (TypeError, ValueError):
                pass
        if max_val is not None:
            try:
                if float(value) > float(max_val):
                    errors[name] = f"{col.label} must be ≤ {max_val}."
                    continue
            except (TypeError, ValueError):
                pass

        # regex_pattern
        pattern = getattr(col, "regex_pattern", None)
        if pattern and isinstance(value, str):
            try:
                if not re.match(pattern, value):
                    errors[name] = f"{col.label} format is invalid."
                    continue
            except re.error:
                pass

        # unique (DB check)
        if getattr(col, "unique", False):
            try:
                from arasCore.admin.table_registry import get_model_for_table
                model = get_model_for_table(col.table_id)
                if model:
                    dup = model.query.filter(
                        getattr(model, name) == value
                    ).first()
                    if dup and (existing_obj is None or dup.id != getattr(existing_obj, "id", None)):
                        errors[name] = f"{col.label} must be unique."
            except Exception as e:
                logger.debug(f"[validator] unique check failed for {name}: {e}")

    return errors
