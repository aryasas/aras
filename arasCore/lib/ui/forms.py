# -*- coding: utf-8 -*-
"""
arasCore/lib/ui/forms.py — single form layer.

Re-exports ArasForm + helpers used across admin layers. The canonical way
to build a form for a model is ``Model.form(data=..., obj=...)`` (see
``ArasModel.form()``), which delegates to ``ArasForm.from_model``.

``build_form_from_table(tbl)`` is the dynamic-app counterpart used when
the model is generated at runtime from ``AppManagerTable`` rows.
"""
from __future__ import annotations
import logging

from arasCore.aras_gen import ArasForm, Col, String

logger = logging.getLogger(__name__)


# Columns that should never appear in admin forms (system bookkeeping).
_CORE_SYSTEM_INTERNAL = {
    "id", "created_at", "updated_at", "created_by", "updated_by",
    "deleted_at", "deleted_by",
}


class BasicForm(ArasForm):
    """ArasForm preset with read-only audit fields hidden from forms."""
    pass


def build_form_from_table(tbl) -> type[ArasForm]:
    """Build an ArasForm subclass from a dynamic AppManagerTable + its columns.

    Returns a class (not an instance). Caller does ``FormCls(data=..., obj=...)``.
    """
    from arasCore.aras_gen.fields import (
        Col, String, Text, Integer, Decimal, Float, Boolean, Date, DateTime,
        Password, Email, Select, FK,
    )

    type_map = {
        "string":   String,  "varchar": String,
        "text":     Text,
        "integer":  Integer, "int":     Integer, "bigint": Integer,
        "decimal":  Decimal, "numeric": Decimal,
        "float":    Float,
        "boolean":  Boolean, "bool":    Boolean,
        "date":     Date,
        "datetime": DateTime,
        "password": Password,
        "email":    Email,
        "select":   Select, "enum":    Select,
        "relation": FK,     "fk":      FK,
    }

    ns: dict[str, Col] = {}
    cols = tbl.get_columns() if hasattr(tbl, "get_columns") else []
    for c in cols:
        if c.name in _CORE_SYSTEM_INTERNAL:
            continue
        if not getattr(c, "show_in_form", True):
            continue
        token = type_map.get((c.field_type or "string").lower(), String)
        kwargs = {
            "label":  c.label or c.name.replace("_", " ").title(),
            "null":   bool(getattr(c, "nullable", True)),
        }
        if hasattr(c, "default") and c.default not in (None, ""):
            kwargs["default"] = c.default
        if hasattr(c, "max_length") and c.max_length:
            kwargs["length"] = c.max_length
        if c.field_type in ("relation", "fk") and getattr(c, "relation_table_id", None):
            try:
                from arasCore.admin.models import AppManagerTable
                ref = AppManagerTable.query.get(c.relation_table_id)
                if ref:
                    kwargs["fk"] = f"{ref.db_table_name or ref.name}.id"
            except Exception:
                pass
        ns[c.name] = Col(token, **kwargs) if not callable(token) or token.__name__ == "Col" else Col(token, **kwargs)

    cls_name = f"DynForm_{getattr(tbl, 'db_table_name', None) or getattr(tbl, 'name', 'Table')}"
    return type(cls_name, (ArasForm,), ns)


__all__ = ["ArasForm", "BasicForm", "build_form_from_table", "_CORE_SYSTEM_INTERNAL"]
