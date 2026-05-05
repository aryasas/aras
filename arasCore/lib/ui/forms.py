from arasCore.lib.core.aras_base import ArasBase
from flask_wtf import FlaskForm
from wtforms import HiddenField
from wtforms_components import read_only, StringField


class ArasForm(FlaskForm, ArasBase):
    """Base form for all forms in aras. Every form must inherit from this."""

    @classmethod
    def from_columns(cls, columns: list, extra_fields: dict = None) -> type:
        """
        Factory: build an ArasForm subclass from a list of AppManagerColumn instances.
        extra_fields: additional WTForms field instances (override or append).
        Returns a Form class (not an instance).
        """
        from arasCore.admin.services import _make_wtf_field
        from wtforms import SelectField as SF
        from wtforms.validators import Optional as Opt

        from arasCore.lib.ui.label_utils import humanize
        form_attrs = {}
        for col in columns:
            lbl = col.label if col.label and col.label != col.name else humanize(col.name)
            if col.field_type == "relation" and col.relation_table_id:
                _base = col.name[:-3] if col.name.endswith("_id") else col.name
                _rf = getattr(col, "relation_filter", None) or None
                form_attrs[f"{_base}_id"] = SF(lbl, coerce=int, validators=[Opt()],
                                               validate_choice=False,
                                               render_kw={"data-relation-filter": _rf or ""})
            else:
                form_attrs[col.name] = _make_wtf_field(col)

        if extra_fields:
            form_attrs.update(extra_fields)

        return type("DynamicArasForm", (cls,), form_attrs)

    def render_fields(self) -> list:
        """
        Return [(field, field_name), ...] skipping HiddenField and csrf_token.
        Useful for templates that need field metadata.
        """
        result = []
        for name, field in self._fields.items():
            if name == "csrf_token":
                continue
            if isinstance(field, HiddenField):
                continue
            result.append((field, name))
        return result


class BasicForm(ArasForm):
    """ArasForm with audit fields (id, timestamps, user) rendered as read-only."""

    id         = StringField("Id")
    created_at = StringField("Created At")
    updated_at = StringField("Modified At")
    created_by = StringField("Created By")
    updated_by = StringField("Updated By")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fname in ("id", "created_at", "updated_at", "created_by", "updated_by"):
            field = getattr(self, fname, None)
            if field is not None:
                read_only(field)


# Minimal core safety list for fields that should NEVER be manually added to forms
_CORE_SYSTEM_INTERNAL = {"id", "csrf_token", "deleted_at", "tenant_id", "owner_id"}

def build_form_from_table(tbl, extra_columns=None) -> type:
    """
    Build an ArasForm subclass from AppManagerTable + optional extra AppManagerColumn list.
    Respects the 'show_in_form' attribute from mgr_column metadata.
    """
    # Use metadata show_in_form + minimal safety guard
    columns = [
        c for c in tbl.get_columns() 
        if c.show_in_form and c.name not in _CORE_SYSTEM_INTERNAL
    ]

    if extra_columns:
        existing_names = {c.name for c in columns}
        for ec in extra_columns:
            if ec.name not in existing_names and getattr(ec, "show_in_form", True) and ec.name not in _CORE_SYSTEM_INTERNAL:
                columns.append(ec)
        columns.sort(key=lambda c: getattr(c, "order", 0) or 0)

    return ArasForm.from_columns(columns)
