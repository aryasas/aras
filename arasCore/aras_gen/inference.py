# -*- coding: utf-8 -*-
"""
arasCore/aras_gen/inference.py
==============================
Infer a field's type from its attribute name, so users can write::

    password = Col(null=False)            # → Password
    email    = Col(unique=True)           # → Email
    is_admin = Col(default=False)         # → Boolean
    birth    = Col()                      # → Date (suffix '_birth' / 'birth')
    company_id = Col(fk='companies.id')   # → FK
    description = Col()                   # → Text

Explicit type wins: ``String(...)`` always returns String regardless of name.
"""
from __future__ import annotations
from .fields import (
    String, Text, Integer, Boolean, Date, DateTime,
    Password, Email, FK, Decimal,
)


# Order matters: more-specific suffixes / exact names first.
_RULES: list[tuple[callable, object]] = [
    (lambda n: n == "passwd" or "password" in n,                   Password),
    (lambda n: n == "email" or n.endswith("_email"),               Email),
    (lambda n: n.endswith("_at") or n in ("created_at", "updated_at", "deleted_at"),
                                                                   DateTime),
    (lambda n: n.endswith("_date") or n.endswith("date") or n in ("birth", "dob"),
                                                                   Date),
    (lambda n: n.startswith("is_") or n.startswith("has_") or n.endswith("_flag"),
                                                                   Boolean),
    (lambda n: n.endswith("_id") and n != "id",                    FK),
    (lambda n: n in ("description", "notes", "note", "remark", "remarks", "body", "content"),
                                                                   Text),
    (lambda n: n in ("amount", "price", "cost", "total", "rate", "qty", "quantity"),
                                                                   Decimal),
    (lambda n: n in ("count", "number", "no", "order"),            Integer),
]


def infer_type(name: str):
    """Return a type token guessed from a field name. Defaults to String."""
    for test, token in _RULES:
        if test(name):
            return token
    return String


__all__ = ["infer_type"]
