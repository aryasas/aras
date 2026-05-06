# -*- coding: utf-8 -*-
"""
arasCore/aras_gen/fields.py
===========================
Declarative field descriptors. One source of truth for:
  * SQLAlchemy column generation
  * Form widget selection
  * Server-side validation
  * Auto-generated metadata for the GUI builder
"""
from __future__ import annotations
from typing import Any, Optional


# ── Type tokens ─────────────────────────────────────────────────────────────

class _Type:
    """Tiny sentinel — describes the *kind* of a field, not its storage."""
    __slots__ = ("name", "py", "widget")
    def __init__(self, name: str, py: type, widget: str):
        self.name, self.py, self.widget = name, py, widget
    def __repr__(self): return self.name


String   = _Type("String",   str,   "text")
Text     = _Type("Text",     str,   "textarea")
Integer  = _Type("Integer",  int,   "number")
Decimal  = _Type("Decimal",  float, "number")
Float    = _Type("Float",    float, "number")
Boolean  = _Type("Boolean",  bool,  "checkbox")
Date     = _Type("Date",     str,   "date")
DateTime = _Type("DateTime", str,   "datetime-local")
Password = _Type("Password", str,   "password")
Email    = _Type("Email",    str,   "email")
Select   = _Type("Select",   str,   "select")
FK       = _Type("FK",       int,   "select")


# ── The field descriptor ────────────────────────────────────────────────────

class Col:
    """Field declaration — owns metadata, widget hint, and constraints.

    Translated to db.Column at model-class creation, kept on the model as
    `_aras_fields[name] = Col(...)` for forms / GUI / API to introspect.
    """
    __slots__ = (
        "type", "null", "default", "unique", "index", "primary",
        "fk", "choices", "label", "help_text",
        "show_in_form", "show_in_list", "readonly",
        "length", "name", "_explicit", "_owner_table",
    )

    def __init__(
        self,
        type: _Type | None = None,
        *,
        null: bool = True,
        default: Any = None,
        unique: bool = False,
        index: bool = False,
        primary: bool = False,
        fk: str | None = None,
        choices: list | None = None,
        label: str | None = None,
        help_text: str | None = None,
        show_in_form: bool = True,
        show_in_list: bool = True,
        readonly: bool = False,
        length: int | None = None,
    ):
        self.type         = type if type is not None else None  # may be inferred later
        self._explicit    = type is not None
        self.null         = null
        self.default      = default
        self.unique       = unique
        self.index        = index
        self.primary      = primary
        self.fk           = fk
        self.choices      = choices or []
        self.label        = label
        self.help_text    = help_text
        self.show_in_form = show_in_form
        self.show_in_list = show_in_list
        self.readonly     = readonly
        self.length       = length
        self.name         = ""  # set by metaclass
        self._owner_table = ""  # set by metaclass after class creation

    def resolved_label(self) -> str:
        """Single source of truth for labels: mgr_column row > code-declared > humanized name.
        DB row is auto-seeded on first read so the GUI has something to edit."""
        from arasCore.aras_gen.labels import resolve_label
        return resolve_label(self._owner_table, self.name, self.label)

    # GUI / API contract
    def to_schema(self) -> dict:
        return {
            "name":         self.name,
            "type":         (self.type or String).name,
            "widget":       (self.type or String).widget,
            "label":        self.resolved_label(),
            "required":     not self.null and not self.primary,
            "readonly":     self.readonly,
            "default":      self.default,
            "choices":      self.choices,
            "fk":           self.fk,
            "help_text":    self.help_text,
            "show_in_form": self.show_in_form,
            "show_in_list": self.show_in_list,
            "length":       self.length,
        }


__all__ = [
    "Col", "String", "Text", "Integer", "Decimal", "Float", "Boolean",
    "Date", "DateTime", "Password", "Email", "Select", "FK",
]
