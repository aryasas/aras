# -*- coding: utf-8 -*-
"""SQLAlchemy column and WTForms field factories for dynamic tables."""
from arasCore.lib.core.extensions import db
from arasCore.lib.ui.label_utils import humanize as _humanize_label

# ── SA column dispatch ────────────────────────────────────────────────────────

def _make_sa_column(col):
    """Build a SQLAlchemy Column from an AppManagerColumn instance."""
    ft      = col.field_type
    nl      = not col.required
    uniq    = getattr(col, "unique", False)
    maxlen  = getattr(col, "max_length", None) or col.length or 200

    _simple = {
        "string":   lambda: db.Column(db.String(maxlen), nullable=nl, unique=uniq),
        "email":    lambda: db.Column(db.String(maxlen), nullable=nl, unique=uniq),
        "phone":    lambda: db.Column(db.String(maxlen), nullable=nl, unique=uniq),
        "url":      lambda: db.Column(db.String(500), nullable=nl),
        "select":   lambda: db.Column(db.String(100), nullable=nl),
        "uuid":     lambda: db.Column(db.String(100), nullable=nl),
        "file":     lambda: db.Column(db.String(500), nullable=nl),
        "image":    lambda: db.Column(db.String(500), nullable=nl),
        "text":     lambda: db.Column(db.Text, nullable=nl),
        "integer":  lambda: db.Column(db.Integer, nullable=nl),
        "float":    lambda: db.Column(db.Float, nullable=nl),
        "decimal":  lambda: db.Column(db.Numeric(10, 2), nullable=nl),
        "boolean":  lambda: db.Column(db.Boolean, default=False),
        "date":     lambda: db.Column(db.Date, nullable=nl),
        "datetime": lambda: db.Column(db.DateTime, nullable=nl),
        "json":     lambda: db.Column(db.JSON, nullable=nl),
    }
    if ft in _simple:
        return _simple[ft]()
    if ft == "relation":
        if col.relation_table_id:
            return None  # handled in make_table_model
        if col.relation_system_table:
            return db.Column(db.Integer, db.ForeignKey(f"{col.relation_system_table}.id"), nullable=nl)
    return db.Column(db.String(200), nullable=nl)


# ── WTForms field dispatch ────────────────────────────────────────────────────

def _make_wtf_field(col):
    """Build a WTForms field from an AppManagerColumn instance."""
    from wtforms import (StringField, TextAreaField, IntegerField,
                         BooleanField, DateField, SelectField, FileField)
    from wtforms.validators import DataRequired, Optional as Opt, Email, URL, Length, NumberRange

    label      = col.label if col.label and col.label != col.name else _humanize_label(col.name)
    validators = [DataRequired()] if col.required else [Opt()]
    render_kw  = {}
    description = getattr(col, "help_text", None) or ""

    max_len = getattr(col, "max_length", None)
    if max_len:
        validators.append(Length(max=max_len))

    min_v, max_v = getattr(col, "min_value", None), getattr(col, "max_value", None)
    if min_v is not None or max_v is not None:
        try:
            validators.append(NumberRange(
                min=float(min_v) if min_v else None,
                max=float(max_v) if max_v else None,
            ))
        except (TypeError, ValueError):
            pass

    placeholder = getattr(col, "placeholder", None)
    if placeholder:
        render_kw["placeholder"] = placeholder

    kw = dict(validators=validators, render_kw=render_kw, description=description)
    ft = col.field_type

    if ft == "text":     return TextAreaField(label, **kw)
    if ft == "integer":  return IntegerField(label, **kw)
    if ft == "boolean":  return BooleanField(label, description=description)
    if ft == "date":     return DateField(label, **kw)

    if ft in ("float", "decimal"):
        from wtforms import DecimalField
        return DecimalField(label, **kw)

    if ft == "datetime":
        from wtforms.fields import DateTimeLocalField
        return DateTimeLocalField(label, **kw)

    if ft == "email":
        from wtforms.fields import EmailField
        validators.append(Email())
        return EmailField(label, **kw)

    if ft == "url":
        from wtforms.fields import URLField
        validators.append(URL())
        return URLField(label, **kw)

    if ft == "select":
        choices_str = getattr(col, "choices", "") or ""
        opts = [(c.strip(), c.strip()) for c in choices_str.split(",") if c.strip()]
        return SelectField(label, choices=opts, validators=validators, description=description)

    if ft == "relation":
        return SelectField(label, coerce=int, validators=validators,
                           validate_choice=False, description=description)

    if ft in ("file", "image"):
        return FileField(label, description=description)

    if ft == "json":
        return TextAreaField(label, **kw)

    return StringField(label, **kw)
