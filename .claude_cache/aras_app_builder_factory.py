"""
factory.py
==========
Creates SQLAlchemy Models and WTForms Forms dynamically
based on AppBuilderApp and AppBuilderField definitions from the database.
"""
import logging

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, BooleanField, DateField, FloatField
from wtforms.validators import DataRequired, Optional

from aras.lib.db import db, Base

logger = logging.getLogger(__name__)

# Mapping field_type -> (SQLAlchemy column factory, WTForms field class)
COLUMN_MAP = {
    "string":  (lambda: db.Column(db.String(200)),             StringField),
    "text":    (lambda: db.Column(db.Text),                    TextAreaField),
    "integer": (lambda: db.Column(db.Integer),                 IntegerField),
    "boolean": (lambda: db.Column(db.Boolean, default=False),  BooleanField),
    "date":    (lambda: db.Column(db.Date),                    DateField),
    "float":   (lambda: db.Column(db.Float),                   FloatField),
}

# In-process registry to avoid rebuilding models on every request
_model_registry: dict = {}
_form_registry:  dict = {}


def make_dynamic_model(app_def):
    """
    Build a SQLAlchemy Model class from an AppBuilderApp definition.
    Returns the class (not an instance).
    """
    table_name = f"ab_{app_def.name}"
    class_name = f"DynModel_{app_def.name}"

    # Return from our cache first
    if table_name in _model_registry:
        logger.debug(f"[factory] Model cache hit: {table_name}")
        return _model_registry[table_name]

    # Check SQLAlchemy's declarative registry — the class may already exist
    # even if our dict was cleared (e.g. after clear_cache).
    # Re-using it avoids "Multiple classes found for path" mapper errors.
    try:
        existing = Base.registry._class_registry.get(class_name)
    except Exception:
        existing = None
    if existing is not None:
        logger.debug(f"[factory] Model found in SA registry: {class_name}")
        _model_registry[table_name] = existing
        return existing

    # Collect dynamic field columns
    attrs = {
        "__tablename__": table_name,
        "__table_args__": {"extend_existing": True},
    }

    for field in app_def.get_fields():
        col_factory, _ = COLUMN_MAP.get(field.field_type, COLUMN_MAP["string"])
        col = col_factory()
        if field.required:
            col.nullable = False
        attrs[field.name] = col

    # Standard methods required by manager.py and Base
    def __repr__(self):
        return f"<{app_def.name} id={self.id}>"

    def add_parent_id(self, parent_id):
        pass

    # Override Base.on_add — manager.py sets created_by_id directly.
    def on_add(self):
        pass

    # Required by Base.format_search_column -> ListView search
    field_names_snapshot = [f.name for f in app_def.get_fields()]
    def set_searchable_columns(self, _fields=field_names_snapshot):
        return [(name, None, None) for name in _fields]

    attrs["__repr__"]               = __repr__
    attrs["on_add"]                 = on_add
    attrs["add_parent_id"]          = add_parent_id
    attrs["set_searchable_columns"] = set_searchable_columns

    DynamicModel = type(class_name, (Base,), attrs)

    _model_registry[table_name] = DynamicModel
    logger.info(f"[factory] Model created: {class_name} -> table {table_name}")
    return DynamicModel


def make_dynamic_form(app_def, model_class):
    """
    Build a WTForms Form class from an AppBuilderApp definition.
    Returns the class (not an instance).
    """
    form_key = f"{app_def.name}_form"

    if form_key in _form_registry:
        logger.debug(f"[factory] Form cache hit: {form_key}")
        return _form_registry[form_key]

    form_attrs = {}
    for field in app_def.get_fields():
        _, FormField = COLUMN_MAP.get(field.field_type, COLUMN_MAP["string"])
        validators = [DataRequired()] if field.required else [Optional()]
        form_attrs[field.name] = FormField(field.label, validators=validators)

    DynamicForm = type(f"{app_def.name.capitalize()}Form", (FlaskForm,), form_attrs)

    _form_registry[form_key] = DynamicForm
    logger.info(f"[factory] Form created: {DynamicForm.__name__}")
    return DynamicForm


def get_view_columns(app_def):
    """
    Build view_columns list for ModuleRegistry.
    Format: [("Label", "field_name"), ...]
    """
    return [(f.label, f.name) for f in app_def.get_fields()]


def clear_cache(app_name=None):
    """Clear cached model/form for a specific app or all apps."""
    if app_name:
        _model_registry.pop(f"ab_{app_name}", None)
        _form_registry.pop(f"{app_name}_form", None)
    else:
        _model_registry.clear()
        _form_registry.clear()
