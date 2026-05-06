# -*- coding: utf-8 -*-
"""
arasCore/aras_gen/model.py
==========================
ArasModel — declarative model. Col descriptors compile to db.Column
at class-creation, while the original Col survives in _aras_fields
for forms, API and the GUI builder to introspect.
"""
from __future__ import annotations
from typing import ClassVar

from arasCore.lib.core.extensions import db
from arasCore.lib.core.aras_base import ArasBase
from arasCore.lib.core.base_model import ArasModel as _LegacyArasModel
from .inference import infer_type
from .registry  import register
from .fields import (
    Col, _Type,
    String, Text, Integer, Decimal, Float, Boolean,
    Date, DateTime, Password, Email, Select, FK,
)


# ── Type token → SQLAlchemy column type ─────────────────────────────────────

def _sa_type(col: Col):
    t = col.type
    if t is String or t is Password or t is Email or t is Select:
        return db.String(col.length or 255)
    if t is Text:                    return db.Text
    if t is Integer or t is FK:      return db.Integer
    if t is Decimal:                 return db.Numeric(18, 4)
    if t is Float:                   return db.Float
    if t is Boolean:                 return db.Boolean
    if t is Date:                    return db.Date
    if t is DateTime:                return db.DateTime
    return db.String(255)


def _to_sa_column(col: Col) -> db.Column:
    args, kw = [_sa_type(col)], {
        "nullable": col.null,
        "default":  col.default,
        "unique":   col.unique,
        "index":    col.index,
    }
    if col.primary:
        kw["primary_key"] = True
        kw["nullable"]    = False
    if col.fk:
        args.append(db.ForeignKey(col.fk))
    return db.Column(*args, **kw)


# ── Metaclass: compile Col descriptors → db.Column ──────────────────────────

class _ArasModelMeta(type(_LegacyArasModel)):
    """Wraps SQLAlchemy DeclarativeMeta, intercepts Col descriptors."""
    def __new__(mcs, name, bases, ns):
        fields: dict[str, Col] = {}
        # Inherit fields from parents
        for b in bases:
            inherited = getattr(b, "_aras_fields", None)
            if inherited:
                fields.update(inherited)

        # Compile own Col descriptors
        for key, val in list(ns.items()):
            if isinstance(val, Col):
                val.name = key
                if not val._explicit:
                    val.type = infer_type(key)
                fields[key] = val
                ns[key] = _to_sa_column(val)

        ns["_aras_fields"] = fields
        cls = super().__new__(mcs, name, bases, ns)
        # Tag each Col with its owning table so resolved_label() can query mgr_column
        tbl = getattr(cls, "__tablename__", "") or ""
        for col in fields.values():
            if not getattr(col, "_owner_table", ""):
                col._owner_table = tbl
        # Auto-register concrete (non-abstract) models for manifest auto-gen
        if not ns.get("__abstract__", False) and getattr(cls, "__app__", None):
            register(cls)
        return cls


# ── ArasModel — abstract base ───────────────────────────────────────────────

class ArasModel(_LegacyArasModel, ArasBase, metaclass=_ArasModelMeta):
    """Abstract base for all aras app models.

    Inherit it. Declare fields as ``name = Col(...)``. The metaclass
    compiles each Col into a db.Column and keeps the Col on the class
    as ``_aras_fields[name]`` for forms / GUI / API.
    """
    __abstract__ = True

    _aras_fields: ClassVar[dict[str, Col]] = {}

    @classmethod
    def schema(cls) -> list[dict]:
        return [c.to_schema() for c in cls._aras_fields.values()]

    @classmethod
    def form(cls, data: dict | None = None, obj=None, *, exclude=()):
        """Return a bound ArasForm instance for this model. Single source of truth.

        Builds (and caches) a per-model ArasForm subclass from _aras_fields, then
        instantiates it with submitted data and/or an existing object.
        """
        from .form import ArasForm
        cache_attr = "_aras_form_cls"
        FormCls = cls.__dict__.get(cache_attr)
        if FormCls is None:
            FormCls = ArasForm.from_model(cls, exclude=exclude)
            setattr(cls, cache_attr, FormCls)
        return FormCls(data=data, obj=obj)


__all__ = ["ArasModel"]
