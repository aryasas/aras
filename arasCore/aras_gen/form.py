# -*- coding: utf-8 -*-
"""
arasCore/aras_gen/form.py
=========================
ArasForm — schema-driven, no WTForms / FlaskForm.

A form is just:
  * a list of Col descriptors  (declared on subclass, or harvested from a model)
  * a dict of submitted data
  * validate() + populate(obj)

It is rendered server-side by walking ``form.fields`` (list of dicts) or
JSON-served to a frontend builder.
"""
from __future__ import annotations
from typing import Any, Iterable

from arasCore.lib.core.aras_base import ArasBase
from .inference import infer_type
from .fields import Col


# ── Validators (free functions — composable, framework-supplied) ────────────

def _validate(col: Col, value: Any) -> str | None:
    """Return error message, or None if OK."""
    empty = value in (None, "", [])

    if not col.null and not col.primary and empty and col.default is None:
        return f"{col.resolved_label()} is required."

    if empty:
        return None

    py = col.type.py
    try:
        if py is int and not isinstance(value, bool):  int(value)
        elif py is float:                              float(value)
        elif py is bool:
            if isinstance(value, str) and value.lower() not in ("true", "false", "1", "0", "on", "off", "yes", "no"):
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


def _coerce(col: Col, value: Any) -> Any:
    if value in (None, ""):
        return None if col.null else col.default
    py = col.type.py
    try:
        if py is int and not isinstance(value, bool):
            return int(value)
        if py is float:
            return float(value)
        if py is bool:
            if isinstance(value, bool):  return value
            return str(value).lower() in ("true", "1", "on", "yes")
    except (TypeError, ValueError):
        return value
    return value


# ── ArasForm ────────────────────────────────────────────────────────────────

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

    # ------------------------------------------------------------------ ctor

    def __init__(self, data: dict | None = None, obj: Any = None):
        self.data: dict[str, Any] = {}
        self.errors: dict[str, str] = {}

        # Seed from obj first, then overlay submitted data
        if obj is not None:
            for name in self._aras_fields:
                if hasattr(obj, name):
                    self.data[name] = getattr(obj, name)
        if data:
            for name in self._aras_fields:
                if name in data:
                    self.data[name] = data[name]

    # ------------------------------------------------------------------ api

    @classmethod
    def from_model(cls, model_cls, *, exclude: Iterable[str] = ()) -> type["ArasForm"]:
        """Build an ArasForm subclass straight from a model's _aras_fields."""
        excl = set(exclude) | {"id", "created_at", "updated_at", "created_by", "updated_by"}
        ns = {
            name: col
            for name, col in getattr(model_cls, "_aras_fields", {}).items()
            if name not in excl and col.show_in_form
        }
        return type(f"{model_cls.__name__}Form", (cls,), ns)

    @property
    def fields(self) -> list[dict]:
        """List-of-dicts schema — what templates iterate over."""
        return [c.to_schema() for c in self._aras_fields.values()]

    def validate(self) -> bool:
        self.errors.clear()
        for name, col in self._aras_fields.items():
            err = _validate(col, self.data.get(name))
            if err:
                self.errors[name] = err
        return not self.errors

    def populate(self, obj) -> None:
        """Apply coerced data onto an ORM object."""
        for name, col in self._aras_fields.items():
            if col.readonly or col.primary:
                continue
            if name in self.data:
                setattr(obj, name, _coerce(col, self.data[name]))

    # ── Compat shims so callers built around FlaskForm still work ────────

    def populate_obj(self, obj) -> None:
        """FlaskForm-compat alias for populate()."""
        self.populate(obj)

    def validate_on_submit(self) -> bool:
        """True iff request is POST and validate() passes."""
        from flask import request
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return False
        # Pull form data into self.data on submit
        if request.form:
            for name in self._aras_fields:
                if name in request.form:
                    val = request.form.getlist(name)
                    self.data[name] = val[0] if len(val) == 1 else val
        return self.validate()

    def hidden_tag(self) -> str:
        """FlaskForm-compat: render hidden CSRF input. CSRF is handled by
        arasCore.lib.core.csrf, which exposes csrf_token() as a Jinja global,
        so this returns an inline hidden input for templates that call
        ``form.hidden_tag()``."""
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
    """WTForms-shape adapter so templates calling ``form.<name>(...)``,
    ``field.label.text``, ``field.errors``, ``field.flags.required``, ``field.type``,
    ``field.id`` keep working without WTForms installed.

    Renders a minimal HTML widget when called, with attributes spread from kwargs.
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

    # ── duck-typed attributes WTForms users expect ──
    @property
    def name(self): return self._name
    @property
    def id(self):   return self._name
    @property
    def type(self):
        return self._TYPE_MAP.get(self._col.type.name, "StringField")
    @property
    def label(self):
        text = self._col.resolved_label()
        return type("_Lbl", (), {"text": text})()
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
        return self._form.data.get(self._name)
    @property
    def choices(self):
        return getattr(self._col, "_fk_choices", None) or self._col.choices or []

    def __call__(self, **kw):
        from markupsafe import Markup, escape
        col = self._col
        widget = col.type.widget
        val = self._form.data.get(self._name, "")
        attrs = {"name": self._name, "id": self._name}
        if kw.get("class_"):
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
        # default: input
        v_attr = f' value="{escape(str(val))}"' if val not in (None, "") else ""
        return Markup(f'<input type="{widget}" {attrs_str}{v_attr}>')


# Patch ArasForm with proxy access + iter helpers.
def _form_getattr(self, name):
    fields = type(self).__dict__.get("_aras_fields") or self._aras_fields
    if name in fields:
        return _FieldProxy(self, name, fields[name])
    raise AttributeError(name)


def _form_iter(self):
    for n, c in self._aras_fields.items():
        yield _FieldProxy(self, n, c)


ArasForm.__getattr__ = _form_getattr
ArasForm.__iter__    = _form_iter


__all__ = ["ArasForm"]
