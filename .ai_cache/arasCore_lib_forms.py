from flask_wtf import FlaskForm
from wtforms import HiddenField
from wtforms_components import read_only, StringField


class ArasForm(FlaskForm):
    """Base form for all forms in aras. Every form must inherit from this."""

    @classmethod
    def from_columns(cls, columns: list, extra_fields: dict = None) -> type:
        """
        Factory: build an ArasForm subclass from a list of AppManagerColumn instances.
        extra_fields: additional WTForms field instances (override or append).
        Returns a Form class (not an instance).
        """
        from arasCore.arasAdmin.services import _make_wtf_field
        from wtforms import SelectField as SF
        from wtforms.validators import Optional as Opt

        form_attrs = {}
        for col in columns:
            if col.field_type == "relation" and col.relation_table_id:
                form_attrs[f"{col.name}_id"] = SF(col.label, coerce=int, validators=[Opt()])
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


def build_form_from_table(tbl, extra_columns=None) -> type:
    """
    Build an ArasForm subclass from AppManagerTable + optional extra AppManagerColumn list.
    Merges standard columns with extra_columns (e.g. from AppManagerField / doctype settings),
    ordered by the column's `order` attribute.
    Returns a Form class ready to be instantiated in a route.
    """
    columns = list(tbl.get_columns())

    if extra_columns:
        existing_names = {c.name for c in columns}
        for ec in extra_columns:
            if ec.name not in existing_names:
                columns.append(ec)
        columns.sort(key=lambda c: getattr(c, "order", 0) or 0)

    return ArasForm.from_columns(columns)
