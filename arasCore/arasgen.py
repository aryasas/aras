# -*- coding: utf-8 -*-
"""
arasCore/aras_gen.py
====================
Single-file declarative DSL: model + form + route + app + field descriptors.

One import surface. Apps do:

    from arasCore import ArasGen, ArasModel, ArasDoc, ArasApp, Col, String, ...

Replaces the former arasCore/aras_gen/ package. Sections:
    1.  Field type tokens (_TString, ...) + bare-name factories (String, ...)
    2.  Col descriptor
    3.  Name-based type inference
    4.  Label resolver (mgr_column.label > code-declared > humanized)
    5.  ArasDB namespace
    6.  ArasModel + metaclass (Col → db.Column compiler)
    7.  ArasDoc (model + UI meta + handler hooks in one class)
    8.  ArasForm + WTForms-shape proxy
    9.  ArasRoute namespace
    10. Registry + auto_resources / auto_menu_groups
    11. ArasApp (class-style app declaration)
    12. ArasGen umbrella

Naming convention: the *type tokens* live under `_T<Name>` (e.g. `_TString`),
and the bare names `String`, `Integer`, ... are bound to factory callables, so
user code can write `name = String(null=False)` everywhere.
"""
from __future__ import annotations

import logging
import re
from functools import partial
from typing import Any, ClassVar, Iterable, List

from arasCore.lib.core.aras_base import ArasBase
from arasCore.lib.core.base_model import ArasModel as _BaseModel
from arasCore.lib.core.extensions import db as _db

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════════
# 1. Field type tokens
# ════════════════════════════════════════════════════════════════════════════

class _Type:
    """Sentinel — describes the kind of a field, not its storage."""
    __slots__ = ("name", "py", "widget")
    def __init__(self, name: str, py: type, widget: str):
        self.name, self.py, self.widget = name, py, widget
    def __repr__(self): return self.name


_TString   = _Type("String",   str,   "text")
_TText     = _Type("Text",     str,   "textarea")
_TInteger  = _Type("Integer",  int,   "text")
_TDecimal  = _Type("Decimal",  float, "text")
_TFloat    = _Type("Float",    float, "text")
_TBoolean  = _Type("Boolean",  bool,  "checkbox")
_TDate     = _Type("Date",     str,   "date")
_TDateTime = _Type("DateTime", str,   "datetime-local")
_TPassword = _Type("Password", str,   "password")
_TEmail    = _Type("Email",    str,   "email")
_TSelect   = _Type("Select",   str,   "select")
_TFK       = _Type("FK",       int,   "select")


# ════════════════════════════════════════════════════════════════════════════
# 2. Col descriptor
# ════════════════════════════════════════════════════════════════════════════

class Col:
    """Field declaration — owns metadata, widget hint, and constraints.

    Translated to db.Column at model-class creation, kept on the model as
    `_aras_fields[name] = Col(...)` for forms / GUI / API to introspect.
    """
    __slots__ = (
        "type", "null", "default", "unique", "index", "primary",
        "fk", "choices", "label", "help_text",
        "show_in_form", "show_in_list", "readonly",
        "length", "name", "_explicit", "_owner_table", "_fk_choices",
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
        self.type         = type if type is not None else None
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
        self.name         = ""
        self._owner_table = ""
        self._fk_choices  = None

    def resolved_label(self) -> str:
        """mgr_column.label > code-declared > humanized name."""
        return resolve_label(self._owner_table, self.name, self.label)

    def to_schema(self) -> dict:
        return {
            "name":         self.name,
            "type":         (self.type or _TString).name,
            "widget":       (self.type or _TString).widget,
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


def _typed(token: _Type):
    """Col factory bound to a specific type token."""
    f = partial(Col, token)
    f.__doc__ = f"Col with type={token.name}."
    return f


# Bare-name factory aliases — what user code writes: `name = String(null=False)`
String   = _typed(_TString)
Text     = _typed(_TText)
Integer  = _typed(_TInteger)
Decimal  = _typed(_TDecimal)
Float    = _typed(_TFloat)
Boolean  = _typed(_TBoolean)
Date     = _typed(_TDate)
DateTime = _typed(_TDateTime)
Password = _typed(_TPassword)
Email    = _typed(_TEmail)
Select   = _typed(_TSelect)
FK       = _typed(_TFK)


# ════════════════════════════════════════════════════════════════════════════
# 3. Name-based type inference
# ════════════════════════════════════════════════════════════════════════════

_INFER_RULES: list[tuple[callable, _Type]] = [
    (lambda n: n == "passwd" or "password" in n,                                _TPassword),
    (lambda n: n == "email" or n.endswith("_email"),                            _TEmail),
    (lambda n: n.endswith("_at") or n in ("created_at", "updated_at", "deleted_at"),
                                                                                _TDateTime),
    (lambda n: n.endswith("_date") or n.endswith("date") or n in ("birth", "dob"),
                                                                                _TDate),
    (lambda n: n.startswith("is_") or n.startswith("has_") or n.endswith("_flag"),
                                                                                _TBoolean),
    (lambda n: n.endswith("_id") and n != "id",                                 _TFK),
    (lambda n: n in ("description", "notes", "note", "remark", "remarks", "body", "content"),
                                                                                _TText),
    (lambda n: n in ("amount", "price", "cost", "total", "rate", "qty", "quantity"),
                                                                                _TDecimal),
    (lambda n: n in ("count", "number", "no", "order"),                         _TInteger),
]


def infer_type(name: str) -> _Type:
    """Return a type token guessed from a field name. Defaults to String."""
    for test, token in _INFER_RULES:
        if test(name):
            return token
    return _TString


# ════════════════════════════════════════════════════════════════════════════
# 4. Label resolver
# ════════════════════════════════════════════════════════════════════════════

def _humanize(name: str) -> str:
    return name.replace("_", " ").title() if name else ""


def _label_cache():
    from flask import g, has_request_context
    if has_request_context():
        c = getattr(g, "_aras_label_cache", None)
        if c is None:
            c = {}
            g._aras_label_cache = c
        return c
    return None


def resolve_label(table: str, name: str, code_label: str | None) -> str:
    from flask import has_app_context
    fallback = code_label or _humanize(name)
    if not table or not name or not has_app_context():
        return fallback

    cache = _label_cache()
    key = (table, name)
    if cache is not None and key in cache:
        return cache[key]

    try:
        from arasCore.admin.models import AppManagerColumn, AppManagerTable
        row = (
            _db.session.query(AppManagerColumn.label)
            .join(AppManagerTable, AppManagerColumn.table_id == AppManagerTable.id)
            .filter(AppManagerTable.name == table, AppManagerColumn.name == name)
            .first()
        )
        if row and row[0]:
            label = row[0]
        else:
            label = fallback
            _seed_mgr_column(table, name, label)
    except Exception as e:
        logger.debug(f"[label] resolve fail {table}.{name}: {e}")
        label = fallback

    # Translate label if locale is non-English
    try:
        from arasCore.lib.arasgen.translation import _t
        label = _t(label, context_type="label", context_key=f"{table}.{name}")
    except Exception:
        pass

    if cache is not None:
        cache[key] = label
    return label


def _seed_mgr_column(table: str, name: str, label: str) -> None:
    """Best-effort seed so the GUI has a row to edit. No-op on failure."""
    try:
        from arasCore.admin.models import AppManagerColumn, AppManagerTable
        tbl = _db.session.query(AppManagerTable).filter_by(name=table).first()
        if not tbl:
            return
        if _db.session.query(AppManagerColumn.id).filter_by(table_id=tbl.id, name=name).first():
            return
        _db.session.add(AppManagerColumn(table_id=tbl.id, name=name, label=label, field_type="string"))
        _db.session.commit()
    except Exception:
        try:
            _db.session.rollback()
        except Exception:
            pass


# ════════════════════════════════════════════════════════════════════════════
# 5. ArasDB namespace
# ════════════════════════════════════════════════════════════════════════════

class ArasDB:
    """Namespace for DB primitives. Use ``ArasGen.DB.session`` etc."""
    db           = _db
    session      = _db.session
    Column       = _db.Column
    relationship = _db.relationship
    ForeignKey   = _db.ForeignKey


# ════════════════════════════════════════════════════════════════════════════
# 6. ArasModel + metaclass
# ════════════════════════════════════════════════════════════════════════════

def _sa_type(col: Col):
    t = col.type
    if t is _TString or t is _TPassword or t is _TEmail or t is _TSelect:
        return _db.String(col.length or 255)
    if t is _TText:                  return _db.Text
    if t is _TInteger or t is _TFK:  return _db.Integer
    if t is _TDecimal:               return _db.Numeric(18, 4)
    if t is _TFloat:                 return _db.Float
    if t is _TBoolean:               return _db.Boolean
    if t is _TDate:                  return _db.Date
    if t is _TDateTime:              return _db.DateTime
    return _db.String(255)


def _to_sa_column(col: Col):
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
        args.append(_db.ForeignKey(col.fk))
    return _db.Column(*args, **kw)


def _snake(name: str) -> str:
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    return s.lower()


def _module_attrs(mod_cls):
    """Extract (app_name, module_name, menu_title, icon, order) from a module class."""
    if mod_cls is None:
        return None, None, None, "fa-folder", 50
    # Walk MRO to find the app root (class whose parent is ArasApp directly)
    app_name = None
    for c in mod_cls.__mro__:
        if c.__name__ == "ArasApp":
            break
        nm = getattr(c, "name", None) or _snake(c.__name__)
        app_name = nm  # last non-ArasApp wins → top of chain
    # module_name = the immediate class
    module_name = getattr(mod_cls, "name", None) or _snake(mod_cls.__name__)
    title = getattr(mod_cls, "title", None) or _title_split(mod_cls.__name__)
    icon  = getattr(mod_cls, "icon", None) or "fa-folder"
    order = getattr(mod_cls, "order", 50)
    return app_name, module_name, title, icon, order


_DOC_HOOK_NAMES = (
    "list", "before_create", "after_create",
    "before_update", "after_update", "before_delete",
    "serialize", "detail_context", "child_table_actions", "column_setup",
)


def _build_handler_from_class(cls):
    own = {k: v for k, v in cls.__dict__.items() if k in _DOC_HOOK_NAMES and callable(v)}
    if not own:
        return None
    from arasCore.lib.services.app_helper import SubHandler

    class _DocHandler(SubHandler):
        pass

    for hook_name, fn in own.items():
        def _make(fn):
            def _wrapped(self, *a, **kw):
                return fn(self, *a, **kw)
            _wrapped.__name__ = fn.__name__
            return _wrapped
        setattr(_DocHandler, hook_name, _make(fn))
    return _DocHandler()


class _ArasModelMeta(type(_BaseModel)):
    """Wraps SQLAlchemy DeclarativeMeta, intercepts Col descriptors.

    Supports `module=ModuleClass` kwarg on subclass declaration:
        class Invoice(ArasModel, module=Accounting):
            ...
    The metaclass derives __app__, __module__, __tablename__, _aras_meta from the module.
    """
    def __new__(mcs, name, bases, ns, *, module=None, **kw):
        # 1. Module-driven defaults (only when class doesn't override)
        if module is not None:
            app_name, mod_name, mod_title, mod_icon, mod_order = _module_attrs(module)
            if app_name and "__app__" not in ns:
                ns["__app__"] = app_name
            if mod_name and "__aras_module__" not in ns:
                ns["__aras_module__"] = mod_name
            # Auto tablename: {app}_{module}_{snake_class}
            if "__tablename__" not in ns and app_name and mod_name:
                ns["__tablename__"] = f"{app_name}_{mod_name}_{_snake(name)}"
            # Auto menu icon/order from module if not set on class
            if "__menu__" not in ns and mod_title:
                ns["__menu__"] = mod_title
            if "__menu_order__" not in ns:
                ns["__menu_order__"] = mod_order
            ns.setdefault("_aras_module_cls", module)

        # 2. Original Col-compilation logic
        fields: dict[str, Col] = {}
        for b in bases:
            inherited = getattr(b, "_aras_fields", None)
            if inherited:
                fields.update(inherited)

        for key, val in list(ns.items()):
            if isinstance(val, Col):
                val.name = key
                if not val._explicit:
                    val.type = infer_type(key)
                fields[key] = val
                ns[key] = _to_sa_column(val)

        ns["_aras_fields"] = fields
        cls = super().__new__(mcs, name, bases, ns, **kw)
        tbl = getattr(cls, "__tablename__", "") or ""
        for col in fields.values():
            if not getattr(col, "_owner_table", ""):
                col._owner_table = tbl

        # 3. Stamp _aras_meta for views (auto-derived from module + class)
        if not ns.get("__abstract__", False):
            cls._aras_meta = {
                "app":     getattr(cls, "__app__",    None),
                "module":  getattr(cls, "__aras_module__", None),
                "menu":    getattr(cls, "__menu__",   None),
                "title":   getattr(cls, "__title__",  _title_split(name)),
                "icon":    getattr(cls, "__icon__",   "fa-table"),
                "url":     getattr(cls, "__url__",    None),
                "current": name,
            }

        # 4. Auto-derive ArasDoc-style handler if hooks defined on class
        if not ns.get("__abstract__", False):
            existing = ns.get("__handler__")
            if existing is None:
                derived = _build_handler_from_class(cls)
                if derived is not None:
                    cls.__handler__ = derived

        if not ns.get("__abstract__", False) and getattr(cls, "__app__", None):
            register(cls)
        return cls

    def __init__(cls, name, bases, ns, **kw):
        super().__init__(name, bases, ns, **kw)
        if not ns.get("__abstract__", False) and hasattr(cls, '__table__'):
            for col in cls.__table__.columns:
                if col.foreign_keys:
                    fk = next(iter(col.foreign_keys))
                    target_table = fk.target_fullname.split(".")[0]
                    attr_name = col.name.rsplit("_id", 1)[0]
                    if attr_name and not hasattr(cls, attr_name):
                        try:
                            def _resolve(t=target_table):
                                # Check SQLAlchemy registry first
                                if hasattr(_db.Model, "registry"):
                                    registry = _db.Model.registry._class_registry
                                else:
                                    registry = _db.Model._decl_class_registry
                                for c in registry.values():
                                    if hasattr(c, '__tablename__') and c.__tablename__ == t:
                                        return c
                                # Fallback to _MODELS
                                for m in _MODELS:
                                    if getattr(m, "__tablename__", "") == t:
                                        return m
                                # If we absolutely can't find it, raise an error to prevent silent bad mapping
                                raise ValueError(f"Auto-relationship failed: No model found for table '{t}'")
                                
                            setattr(cls, attr_name, _db.relationship(lambda t=target_table: _resolve(t), foreign_keys=[col]))
                        except Exception:
                            pass


class ArasModel(_BaseModel, ArasBase, metaclass=_ArasModelMeta):
    """Abstract base for all aras app models.

    Inherit it. Declare fields as ``name = Col(...)``. The metaclass compiles
    each Col into a db.Column and keeps the Col on the class as
    ``_aras_fields[name]`` for forms / GUI / API.
    """
    __abstract__ = True

    _aras_fields: ClassVar[dict[str, Col]] = {}

    # Auto-naming opt-in. Subclass sets:
    #   __naming_series__ = "SINV-{YYYY}-{####}"   (default pattern; GUI can override)
    #   __name_field__    = "name"                  (which field to write into; default "name")
    __naming_series__: ClassVar[str | None] = None
    __name_field__:    ClassVar[str]        = "name"

    def before_save(self, is_new: bool = False):
        super_fn = getattr(super(), "before_save", None)
        if callable(super_fn):
            super_fn(is_new=is_new)
        if not is_new or not self.__naming_series__:
            return
        field = self.__name_field__
        if not hasattr(self, field) or getattr(self, field, None):
            return
        try:
            from app.erp.erp_main.services.doc_series import next_for_table as next_name
            tbl = getattr(self.__class__, "__tablename__", "") or ""
            new_name = next_name(tbl, self.__naming_series__)
            if new_name:
                setattr(self, field, new_name)
        except Exception as e:  # pragma: no cover
            logger.debug(f"[naming] skipped for {self.__class__.__name__}: {e}")

    @classmethod
    def schema(cls) -> list[dict]:
        return [c.to_schema() for c in cls._aras_fields.values()]

    @classmethod
    def form(cls, data: dict | None = None, obj=None, *, exclude=()):
        cache_attr = "_aras_form_cls"
        FormCls = cls.__dict__.get(cache_attr)
        if FormCls is None:
            FormCls = ArasForm.from_model(cls, exclude=exclude)
            setattr(cls, cache_attr, FormCls)
        
        # Pass model's __app__ slug if present
        app_slug = getattr(cls, "__app__", None)
        if app_slug and hasattr(app_slug, "url"):
            app_slug = app_slug.url
        return FormCls(data=data, obj=obj, app_slug=app_slug)


# ════════════════════════════════════════════════════════════════════════════
# 7. ArasDoc — DEPRECATED alias of ArasModel (folded into model + meta)
# ════════════════════════════════════════════════════════════════════════════

# ArasDoc is now an alias of ArasModel — handler auto-derivation moved into
# _ArasModelMeta. Kept for backwards compatibility during the sweep.
ArasDoc = ArasModel


# ════════════════════════════════════════════════════════════════════════════
# 8. ArasForm + WTForms-shape proxy
# ════════════════════════════════════════════════════════════════════════════

def _form_validate(col: Col, value: Any) -> str | None:
    empty = value in (None, "", [])
    if not col.null and not col.primary and empty and col.default is None:
        return f"{col.resolved_label()} is required."
    if empty:
        return None

    py = col.type.py
    try:
        if py is int and not isinstance(value, bool):
            # If value is string, it might be formatted
            if isinstance(value, str):
                from arasCore.lib.core.utils import parse_number
                v = parse_number(value)
                if v is None: raise ValueError()
            else:
                int(value)
        elif py is float:
            if isinstance(value, str):
                from arasCore.lib.core.utils import parse_number
                v = parse_number(value)
                if v is None: raise ValueError()
            else:
                float(value)
        elif py is bool:
            if isinstance(value, str) and value.lower() not in (
                "true", "false", "1", "0", "on", "off", "yes", "no"
            ):
                return f"{col.resolved_label()} must be boolean."
    except (TypeError, ValueError):
        return f"{col.resolved_label()} must be {col.type.name}."

    if col.type.name == "String" and col.length and isinstance(value, str) and len(value) > col.length:
        return f"{col.resolved_label()} must be ≤ {col.length} characters."

    if col.choices:
        valid = {c[0] if isinstance(c, (tuple, list)) else c for c in col.choices}
        if value not in valid and str(value) not in {str(v) for v in valid}:
            return f"{col.resolved_label()} is not a valid choice."

    return None


def _form_coerce(col: Col, value: Any, app_slug: str | None = None) -> Any:
    if value in (None, ""):
        if col.default is not None:
            return col.default
        return None if col.null else col.default
    py = col.type.py
    try:
        if py is int and not isinstance(value, bool):
            if isinstance(value, str):
                from arasCore.lib.core.utils import parse_number
                iv = parse_number(value, app_slug=app_slug)
                if iv is None: return 0
                iv = int(iv)
            else:
                iv = int(value)
            # FK sentinel: "0" from <select> "— Select —" means NULL when FK is nullable
            if iv == 0 and col.fk and col.null:
                return None
            return iv
        if py is float:
            if isinstance(value, str):
                from arasCore.lib.core.utils import parse_number
                return parse_number(value, app_slug=app_slug)
            return float(value)
        if py is bool:
            if isinstance(value, bool):
                return value
            return str(value).lower() in ("true", "1", "on", "yes")
    except (TypeError, ValueError):
        return value
    return value


def _derive_cols_from_sa(model_cls) -> dict[str, Col]:
    """Build Col descriptors from a model's SQLAlchemy columns (legacy support)."""
    from sqlalchemy import inspect as _sa_inspect

    SKIP = {"id", "created_at", "updated_at", "deleted_at",
            "created_by_id", "updated_by_id"}
    out: dict[str, Col] = {}
    try:
        mapper = _sa_inspect(model_cls)
    except Exception:
        return out
    for sa_col in mapper.columns:
        name = sa_col.key
        if name in SKIP or sa_col.primary_key:
            continue
        tname = sa_col.type.__class__.__name__.lower()
        enum_values = None
        if   "enum"     in tname:
            t = _TString
            enum_values = list(getattr(sa_col.type, "enums", None) or [])
        elif "text"     in tname: t = _TText
        elif "bool"     in tname: t = _TBoolean
        elif "datetime" in tname: t = _TDateTime
        elif "date"     in tname: t = _TDate
        elif "numeric"  in tname or "decimal" in tname: t = _TDecimal
        elif "float"    in tname: t = _TFloat
        elif "int"      in tname or "smallint" in tname or "bigint" in tname: t = _TInteger
        else:                     t = _TString
        fk = None
        if sa_col.foreign_keys:
            fk = next(iter(sa_col.foreign_keys)).target_fullname
        length = getattr(sa_col.type, "length", None) if t is _TString else None
        # Form-level nullability: a column with a default (Python or server)
        # should not be required in the form, even if DB-level nullable=False.
        has_default = (
            sa_col.default is not None
            or sa_col.server_default is not None
        )
        readonly_set = set(getattr(model_cls, "__readonly_fields__", None) or [])
        is_readonly = (name in readonly_set)
        form_nullable = bool(sa_col.nullable) or has_default or is_readonly
        col = Col(
            type     = t,
            null     = form_nullable,
            default  = sa_col.default.arg if sa_col.default is not None and hasattr(sa_col.default, "arg") and not callable(sa_col.default.arg) else None,
            unique   = bool(sa_col.unique),
            index    = bool(sa_col.index),
            fk       = fk,
            length   = length,
            readonly = is_readonly,
        )
        col.name = name
        col._owner_table = getattr(model_cls, "__tablename__", "") or ""
        if fk and not col._explicit:
            col.type = infer_type(name) if name.endswith("_id") else t
        if enum_values:
            col.choices = [(v, v.replace("_", " ").title()) for v in enum_values]
        out[name] = col
    return out


class ArasForm(ArasBase):
    """Schema-driven form. Subclass and declare ``Col`` attributes,
    or call ``ArasForm.from_model(MyModel)`` for full automation.
    """

    _aras_fields: dict[str, Col] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        fields: dict[str, Col] = {}
        for b in cls.__mro__[1:]:
            inherited = getattr(b, "_aras_fields", None)
            if inherited:
                fields.update(inherited)
        for key, val in list(cls.__dict__.items()):
            if isinstance(val, Col):
                val.name = key
                if not val._explicit:
                    val.type = infer_type(key)
                fields[key] = val
        cls._aras_fields = fields

    def __init__(self, data: dict | None = None, obj: Any = None, app_slug: str | None = None):
        self.data: dict[str, Any] = {}
        self.errors: dict[str, str] = {}
        self._app_slug = app_slug
        if obj is not None:
            for name in self._aras_fields:
                if hasattr(obj, name):
                    self.data[name] = getattr(obj, name)
        if data:
            for name in self._aras_fields:
                if name in data:
                    self.data[name] = data[name]

    @classmethod
    def from_model(cls, model_cls, *, exclude: Iterable[str] = ()) -> type["ArasForm"]:
        excl = set(exclude) | {"id", "created_at", "updated_at", "created_by", "updated_by",
                               "created_by_id", "updated_by_id", "deleted_at"}
        fields = getattr(model_cls, "_aras_fields", None) or {}
        if not fields:
            fields = _derive_cols_from_sa(model_cls)
        ns = {
            name: col
            for name, col in fields.items()
            if name not in excl and col.show_in_form
        }
        return type(f"{model_cls.__name__}Form", (cls,), ns)

    @property
    def fields(self) -> list[dict]:
        return [c.to_schema() for c in self._aras_fields.values()]

    def validate(self) -> bool:
        self.errors.clear()
        for name, col in self._aras_fields.items():
            err = _form_validate(col, self.data.get(name))
            if err:
                self.errors[name] = err
        return not self.errors

    def populate(self, obj) -> None:
        for name, col in self._aras_fields.items():
            if col.readonly or col.primary:
                continue
            if name in self.data:
                v = _form_coerce(col, self.data[name], app_slug=self._app_slug)
                # Belt-and-suspenders: nullable FK with value 0 → None
                if v == 0 and col.fk and col.null:
                    v = None
                setattr(obj, name, v)

    def populate_obj(self, obj) -> None:
        self.populate(obj)

    def validate_on_submit(self) -> bool:
        from flask import request
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return False
        if request.form:
            for name, col in self._aras_fields.items():
                val_raw = None
                if name in request.form:
                    vals = request.form.getlist(name)
                    # Collapse duplicate inputs (e.g. visible + hidden) to first non-empty
                    nonempty = [v for v in vals if v not in (None, "")]
                    val_raw = (nonempty[0] if nonempty else (vals[0] if vals else ""))
                elif col.type is _TBoolean:
                    # Checkbox: if missing from form data during POST, it means unchecked
                    val_raw = False
                
                if val_raw is not None:
                    self.data[name] = _form_coerce(col, val_raw, app_slug=self._app_slug)

        return self.validate()

    def __getattribute__(self, name):
        # Intercept field access to return _FieldProxy instead of raw Col
        if name.startswith('_') or name in ('data', 'errors'):
            return object.__getattribute__(self, name)
        fields = object.__getattribute__(self, '_aras_fields')
        if name in fields:
            return _FieldProxy(self, name, fields[name])
        return object.__getattribute__(self, name)

    def __iter__(self):
        for n, c in self._aras_fields.items():
            yield _FieldProxy(self, n, c)

    def hidden_tag(self) -> str:
        from markupsafe import Markup
        try:
            from flask import g
            tok = getattr(g, "_csrf_token", None) or ""
            if not tok:
                from arasCore.lib.core.csrf import generate_csrf
                tok = generate_csrf()
        except Exception:
            tok = ""
        return Markup(f'<input type="hidden" name="csrf_token" value="{tok}">')


class _FieldProxy:
    """WTForms-shape adapter so templates that use ``form.<name>(...)``,
    ``field.label.text``, ``field.errors``, ``field.flags.required``, ``field.type``
    keep working without WTForms installed.
    """
    __slots__ = ("_form", "_col", "_name")

    _TYPE_MAP = {
        "String":   "StringField",
        "Text":     "TextAreaField",
        "Integer":  "IntegerField",
        "Decimal":  "DecimalField",
        "Float":    "DecimalField",
        "Boolean":  "BooleanField",
        "Date":     "DateField",
        "DateTime": "DateTimeLocalField",
        "Password": "PasswordField",
        "Email":    "EmailField",
        "Select":   "SelectField",
        "FK":       "SelectField",
    }

    def __init__(self, form, name, col):
        self._form, self._name, self._col = form, name, col

    @property
    def name(self): return self._name
    @property
    def id(self):   return self._name
    @property
    def type(self):
        if self._col.choices or getattr(self._col, "_fk_choices", None):
            return "SelectField"
        return self._TYPE_MAP.get(self._col.type.name, "StringField")
    @property
    def label(self):
        text = self._col.resolved_label()
        return type("_Lbl", (), {
            "text": text,
            "__str__": lambda s: text,
            "__html__": lambda s: text,
        })()
    @property
    def description(self):
        return self._col.help_text or ""
    @property
    def flags(self):
        return type("_F", (), {"required": (not self._col.null and not self._col.primary)})()
    @property
    def errors(self):
        e = self._form.errors.get(self._name)
        return [e] if e else []
    @property
    def render_kw(self):
        return {}
    @property
    def data(self):
        val = self._form.data.get(self._name)
        return _form_coerce(self._col, val, app_slug=getattr(self._form, "_app_slug", None))
    @property
    def choices(self):
        return getattr(self._col, "_fk_choices", None) or self._col.choices or []

    def __call__(self, **kw):
        from markupsafe import Markup, escape
        col = self._col
        widget = "select" if (col.choices or getattr(col, "_fk_choices", None)) else col.type.widget
        val = self._form.data.get(self._name, "")
        
        # Apply formatting to numeric values for display
        # ONLY if widget is NOT 'number' (browsers reject formatted strings in type="number")
        if val not in (None, "") and col.type.name in ("Decimal", "Float", "Integer") and widget != "number":
            try:
                from arasCore.lib.core.utils import format_number
                # Pass app_slug to respect hierarchical formatting
                app_slug = getattr(self._form, "_app_slug", None)
                val = format_number(val, app_slug=app_slug)
            except Exception:
                pass

        attrs = {"name": self._name, "id": self._name}
        if col.readonly:
            attrs["readonly"] = True
        
        # Add class for numeric fields to allow global JS formatting
        if col.type.name in ("Decimal", "Float", "Integer"):
            attrs["class"] = "aras-numeric-input " + kw.get("class_", "")
            if "class_" in kw: del kw["class_"]
        elif kw.get("class_"):
            attrs["class"] = kw.pop("class_")
        
        for k, v in kw.items():
            attrs[k.rstrip("_").replace("_", "-")] = v
        attrs_str = " ".join(f'{k}="{escape(str(v))}"' for k, v in attrs.items() if v not in (None, False))

        if widget == "textarea":
            return Markup(f'<textarea {attrs_str}>{escape(val or "")}</textarea>')
        if widget == "checkbox":
            checked = ' checked' if val in (True, "true", "1", "on", 1) else ""
            return Markup(f'<input type="checkbox" {attrs_str}{checked}>')
        if widget == "select":
            opts = []
            for choice in self.choices:
                if isinstance(choice, (tuple, list)):
                    cv, cl = choice[0], choice[1]
                else:
                    cv = cl = choice
                sel = ' selected' if str(val) == str(cv) else ""
                opts.append(f'<option value="{escape(str(cv))}"{sel}>{escape(str(cl))}</option>')
            return Markup(f'<select {attrs_str}>{"".join(opts)}</select>')
        v_attr = f' value="{escape(str(val))}"' if val not in (None, "") else ""
        return Markup(f'<input type="{widget}" {attrs_str}{v_attr}>')


# ════════════════════════════════════════════════════════════════════════════
# 9. ArasRoute namespace
# ════════════════════════════════════════════════════════════════════════════

try:
    from arasCore.lib.services.app_helper import (
        AppHelper as _AppHelper, MenuGroup as _MenuGroup,
        ResourceDef as _ResourceDef, SubHandler as _SubHandler,
        CustomRoute as _CustomRoute,
    )
except Exception:                       # pragma: no cover
    _AppHelper = _MenuGroup = _ResourceDef = _SubHandler = _CustomRoute = None


class ArasRoute:
    """Namespace for app manifest declarations."""
    App      = _AppHelper
    Menu     = _MenuGroup
    Resource = _ResourceDef
    Handler  = _SubHandler
    Route    = _CustomRoute


# ════════════════════════════════════════════════════════════════════════════
# 10. Registry + auto_resources / auto_menu_groups
# ════════════════════════════════════════════════════════════════════════════

_MODELS: list[type] = []
_ARAS_APP_CLASSES: list[type] = []   # populated by _ArasAppMeta — defined below

# App config registry: (slug → (namespace_menus, namespace_aliases)).
# Populated by register_app_config() for AppHelper-style manifests.
_APP_CONFIG: dict[str, tuple[dict, dict]] = {}


def register_app_config(slug: str, *, namespace_menus: dict | None = None,
                        namespace_aliases: dict | None = None) -> None:
    """Register tablename-driven menu/url config for an app slug.

    Use from AppHelper-style manifests; ArasApp subclasses register automatically
    via class attrs. Safe to call multiple times — last call wins.
    """
    _APP_CONFIG[slug] = (namespace_menus or {}, namespace_aliases or {})



def register(model: type) -> None:
    """Register an ArasModel subclass. Idempotent."""
    if model not in _MODELS:
        _MODELS.append(model)


def models_for(app: str) -> List[type]:
    return [m for m in _MODELS if getattr(m, "__app__", None) == app]


def _kebab(name: str) -> str:
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1-\2", name)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", s)
    return s.lower()


def _title_split(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", " ", name).strip()


def _app_config(app_slug: str) -> tuple[dict, dict]:
    """Return (namespace_menus, namespace_aliases) for a given app slug.

    Sources, first match wins:
      1. register_app_config() shim (used by AppHelper-style manifests)
      2. ArasApp subclass class attrs
    """
    if app_slug in _APP_CONFIG:
        return _APP_CONFIG[app_slug]
    for cls in _ARAS_APP_CLASSES:
        if getattr(cls, "name", None) == app_slug:
            return (
                getattr(cls, "namespace_menus", {}) or {},
                getattr(cls, "namespace_aliases", {}) or {},
            )
    return {}, {}


def _resolve_alias(ns: str, aliases: dict) -> str:
    seen = set()
    while ns in aliases and isinstance(aliases[ns], str) and ns not in seen:
        seen.add(ns)
        ns = aliases[ns]
    return ns


def _split_tablename(tbl: str) -> tuple[str, str]:
    """`acc_sales_invoice` → ('acc', 'sales_invoice')."""
    if not tbl or "_" not in tbl:
        return "", tbl or ""
    ns, _, rest = tbl.partition("_")
    return ns, rest


def _derive_url(model: type) -> str:
    """`__tablename__` → `<ns>/<kebab(rest)>` (or `<kebab(rest)>` when no ns)."""
    tbl = getattr(model, "__tablename__", "") or ""
    cls_name = model.__name__
    if not tbl:
        return _kebab(cls_name)
    app_slug = getattr(model, "__app__", None) or ""
    _, aliases = _app_config(app_slug)
    ns, rest = _split_tablename(tbl)
    if not ns:
        return rest.replace("_", "-")
    ns = _resolve_alias(ns, aliases)
    return f"{ns}/{rest.replace('_', '-')}"


def _derive_menu(model: type) -> tuple[str | None, str, int]:
    """Return (menu_name, icon, order) from app's namespace_menus map."""
    tbl = getattr(model, "__tablename__", "") or ""
    app_slug = getattr(model, "__app__", None) or ""
    menus, aliases = _app_config(app_slug)
    if not menus or not tbl:
        return None, "fa-folder", 50
    ns, _ = _split_tablename(tbl)
    ns = _resolve_alias(ns, aliases)
    entry = menus.get(ns)
    if isinstance(entry, str):
        entry = menus.get(_resolve_alias(entry, aliases))
    if not entry:
        return None, "fa-folder", 50
    if isinstance(entry, (list, tuple)):
        title = entry[0]
        icon  = entry[1] if len(entry) > 1 else "fa-folder"
        order = entry[2] if len(entry) > 2 else 50
        return title, icon, order
    return str(entry), "fa-folder", 50


def _meta(model: type) -> dict:
    cls_name = model.__name__
    derived_menu, derived_menu_icon, derived_menu_order = _derive_menu(model)
    is_child = getattr(model, "__is_child__", False)
    # __show_in_menu__ explicit override — lets child tables also appear as top-level list view
    show_in_menu = getattr(model, "__show_in_menu__", None)
    if show_in_menu is None:
        show_in_menu = getattr(model, "__admin_list__", True) and not is_child
    return {
        "app":           getattr(model, "__app__",   None),
        "menu":          getattr(model, "__menu__",  derived_menu),
        "menu_icon":     derived_menu_icon,
        "title":         getattr(model, "__title__", _title_split(cls_name)),
        "url":           getattr(model, "__url__",   _derive_url(model)),
        "icon":          getattr(model, "__icon__",  "fa-table"),
        "admin_list":    show_in_menu,
        "is_child":      is_child,
        "searchable":    list(getattr(model, "__searchable__", []) or []),
        "filters":       list(getattr(model, "__filters__",    []) or []),
        "menu_order":    getattr(model, "__menu_order__",     derived_menu_order),
        "handler":       getattr(model, "__handler__",       None),
    }


def auto_resources(app: str) -> list:
    Resource = ArasRoute.Resource
    out = []
    for m in models_for(app):
        meta = _meta(m)
        out.append(Resource(
            meta["url"], m,
            admin_list     = meta["admin_list"],
            is_child_table = meta["is_child"],
            menu_title     = meta["title"],
            menu_icon      = meta["icon"],
            searchable     = meta["searchable"],
            filters        = meta["filters"],
            handler        = meta["handler"],
        ))
    return out


def auto_menu_groups(app: str) -> list:
    Menu, Resource = ArasRoute.Menu, ArasRoute.Resource
    buckets: dict[str, list] = {}
    orders:  dict[str, int]  = {}
    icons:   dict[str, str]  = {}

    for m in models_for(app):
        meta = _meta(m)
        if meta["is_child"]:
            grp_name = meta["menu"] or "_"
        else:
            grp_name = meta["menu"] or app.title()
        buckets.setdefault(grp_name, []).append(Resource(
            meta["url"], m,
            admin_list     = meta["admin_list"],
            is_child_table = meta["is_child"],
            menu_title     = meta["title"],
            menu_icon      = meta["icon"],
            searchable     = meta["searchable"],
            filters        = meta["filters"],
            handler        = meta["handler"],
        ))
        orders[grp_name] = min(orders.get(grp_name, 999), meta["menu_order"])
        icons.setdefault(grp_name, meta["menu_icon"])

    out = [
        Menu(name, icons.get(name, "fa-folder"), order=orders[name], resources=res)
        for name, res in buckets.items() if name != "_"
    ]
    if "_" in buckets:
        out.append(Menu("_hidden", "fa-circle-o", order=999, resources=buckets["_"]))
    return out


# ════════════════════════════════════════════════════════════════════════════
# 11. ArasApp — class-style app declaration
# ════════════════════════════════════════════════════════════════════════════

_AUTO = object()


class _ArasAppMeta(type):
    """Compile an ArasApp subclass to an AppHelper instance on class creation."""
    def __new__(mcs, cls_name, bases, ns):
        cls = super().__new__(mcs, cls_name, bases, ns)
        if ns.get("__abstract__", False) or cls_name == "ArasApp":
            return cls

        name = ns.get("name") or getattr(cls, "name", None)
        if not name:
            return cls

        if cls not in _ARAS_APP_CLASSES:
            _ARAS_APP_CLASSES.append(cls)

        AppHelper_ = ArasRoute.App
        if AppHelper_ is None:
            return cls

        menu_groups   = ns.get("menu_groups",   _AUTO)
        resources     = ns.get("resources",     _AUTO)
        custom_routes = ns.get("custom_routes", [])

        if menu_groups is _AUTO and resources is _AUTO:
            menu_groups = auto_menu_groups(name)
            resources   = None
        else:
            menu_groups = None if menu_groups is _AUTO else menu_groups
            resources   = None if resources   is _AUTO else resources

        cls.helper = AppHelper_(
            name            = name,
            title           = ns.get("title", name.title()),
            resources       = resources,
            menu_groups     = menu_groups,
            custom_routes   = custom_routes,
            admin_icon      = ns.get("icon",  "fa-cubes"),
            admin_order     = ns.get("order", 99),
            home_url        = ns.get("home_url"),
            settings_schema = ns.get("settings_schema") or [],
            admin_slug      = ns.get("admin_slug"),
            api_slug        = ns.get("api_slug"),
            template        = ns.get("template"),
        )
        return cls


class ArasApp(metaclass=_ArasAppMeta):
    """Subclass to declare an app. Set `name` (slug) and optional cosmetics.

    Auto-derives menu_groups from ArasModels whose `__app__` matches `name`.
    Override `menu_groups` or `resources` to take manual control.

    Optional class attrs for tablename-driven URL/menu derivation:
        namespace_menus   = {"acc": ("Accounting", "fa-calculator", 1), ...}
        namespace_aliases = {"stk": "stock"}
    """
    __abstract__: ClassVar[bool] = True

    name:  ClassVar[str]  = ""
    title: ClassVar[str]  = ""
    icon:  ClassVar[str]  = "fa-cubes"
    order: ClassVar[int]  = 99

    namespace_menus:   ClassVar[dict] = {}
    namespace_aliases: ClassVar[dict] = {}


# ════════════════════════════════════════════════════════════════════════════
# 11.5 ArasView — Decoupled UI logic
# ════════════════════════════════════════════════════════════════════════════

_DEFERRED_VIEWS = []

class _ArasViewMeta(type):
    def __new__(mcs, name, bases, ns):
        cls = super().__new__(mcs, name, bases, ns)
        if ns.get("__abstract__", False) or name == "ArasView":
            return cls

        target_model = ns.get("__model__")
        if not target_model:
            return cls

        mod_parts = cls.__module__.split('.')
        app_name = mod_parts[1] if len(mod_parts) >= 2 else None
        module_name = mod_parts[2] if len(mod_parts) >= 3 else None

        def _apply():
            model_cls = next((m for m in _MODELS if m.__name__ == target_model), None)
            if not model_cls:
                return False

            for attr in ("__title__", "__icon__", "__menu__", "__menu_order__", 
                         "__display_fields__", "__searchable__", "__filters__", 
                         "__admin_list__", "__is_child__", "__show_in_menu__"):
                if attr in ns:
                    setattr(model_cls, attr, ns[attr])
            
            if app_name and getattr(model_cls, "__app__", None) is None:
                setattr(model_cls, "__app__", app_name)
            if module_name and getattr(model_cls, "__aras_module__", None) is None:
                setattr(model_cls, "__aras_module__", module_name)

            derived_menu, derived_menu_icon, derived_menu_order = _derive_menu(model_cls)
            model_cls._aras_meta.update({
                "app":     getattr(model_cls, "__app__",    app_name),
                "module":  getattr(model_cls, "__aras_module__", module_name),
                "menu":    getattr(model_cls, "__menu__",   derived_menu),
                "title":   getattr(model_cls, "__title__",  _title_split(target_model)),
                "icon":    getattr(model_cls, "__icon__",   "fa-table"),
            })

            handler = _build_handler_from_class(cls)
            if handler:
                model_cls.__handler__ = handler
            return True

        if not _apply():
            _DEFERRED_VIEWS.append(_apply)
            
        return cls

class ArasView(metaclass=_ArasViewMeta):
    __abstract__ = True

# ════════════════════════════════════════════════════════════════════════════
# 12. ArasGen umbrella
# ════════════════════════════════════════════════════════════════════════════

class ArasGen:
    """Umbrella namespace — the only import an app ever needs."""
    Model = ArasModel
    Doc   = ArasDoc
    View  = ArasView
    Form  = ArasForm
    Route = ArasRoute
    DB    = ArasDB

    App         = ArasApp                # base class — `class ERP(ArasGen.App)`
    _AppHelper  = ArasRoute.App          # legacy factory (private)
    Menu        = ArasRoute.Menu
    Resource    = ArasRoute.Resource
    Handler     = ArasRoute.Handler
    CustomRoute = ArasRoute.Route

    auto_resources   = staticmethod(auto_resources)
    auto_menu_groups = staticmethod(auto_menu_groups)

    @staticmethod
    def autodiscover(package_name: str) -> None:
        import importlib
        import pkgutil
        import sys
        
        base_module = sys.modules.get(package_name) or importlib.import_module(package_name)
        
        def walk_packages(path, prefix):
            for info in pkgutil.iter_modules(path, prefix):
                parts = info.name.split('.')
                if any(p in ('models', 'views', 'services') for p in parts):
                    try:
                        importlib.import_module(info.name)
                    except Exception as e:
                        logger.error(f"[autodiscover] Failed to import {info.name}: {e}")
                if info.ispkg:
                    try:
                        mod = sys.modules.get(info.name) or importlib.import_module(info.name)
                        if hasattr(mod, '__path__'):
                            walk_packages(mod.__path__, info.name + '.')
                    except Exception:
                        pass

        if hasattr(base_module, '__path__'):
            walk_packages(base_module.__path__, base_module.__name__ + '.')
            
        global _DEFERRED_VIEWS
        remaining = []
        for apply_fn in _DEFERRED_VIEWS:
            if not apply_fn():
                remaining.append(apply_fn)
        _DEFERRED_VIEWS = remaining

    Col      = Col
    String   = staticmethod(String)
    Text     = staticmethod(Text)
    Integer  = staticmethod(Integer)
    Decimal  = staticmethod(Decimal)
    Float    = staticmethod(Float)
    Boolean  = staticmethod(Boolean)
    Date     = staticmethod(Date)
    DateTime = staticmethod(DateTime)
    Password = staticmethod(Password)
    Email    = staticmethod(Email)
    Select   = staticmethod(Select)
    FK       = staticmethod(FK)


__all__ = [
    "ArasGen", "ArasModel", "ArasDoc", "ArasForm", "ArasRoute", "ArasDB", "ArasApp",
    "Col", "String", "Text", "Integer", "Decimal", "Float", "Boolean",
    "Date", "DateTime", "Password", "Email", "Select", "FK",
    "auto_resources", "auto_menu_groups", "register", "models_for", "register_app_config",
    "resolve_label", "infer_type",
]
