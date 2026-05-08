# -*- coding: utf-8 -*-
"""arasgen.core — shared primitives.

Re-exports from arasCore.arasgen during transition. Once Phase 6 cleanup is
done, the real definitions move into this package.
"""
from arasCore.arasgen import (
    Col, String, Text, Integer, Decimal, Float, Boolean,
    Date, DateTime, Password, Email, Select, FK,
    infer_type, resolve_label, ArasDB,
)

__all__ = [
    "Col", "String", "Text", "Integer", "Decimal", "Float", "Boolean",
    "Date", "DateTime", "Password", "Email", "Select", "FK",
    "infer_type", "resolve_label", "ArasDB",
]
