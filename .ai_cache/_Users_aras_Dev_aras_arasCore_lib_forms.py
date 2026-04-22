from flask_wtf import FlaskForm
from wtforms_components import read_only, StringField, SelectField
from arasCore.lib.extensions import db
from wtforms_alchemy import model_form_factory
from wtforms import SubmitField


BaseModelForm = model_form_factory(FlaskForm)


class ModelForm(BaseModelForm):
    @classmethod
    def get_session(self):
        return db.session


class EmptyForm(ModelForm):
    class Meta:
        __abstract__ = True


class SubmitForm(ModelForm):
    class Meta:
        __abstract__ = True

    submit = SubmitField("Submit")


class BasicForm(ModelForm):
    class Meta:
        __abstract__ = True

    id = StringField("Id")
    created_at = StringField("Created At")
    updated_at = StringField("Modified At")
    created_by = StringField("Created By")
    updated_by = StringField("Updated By")

    def __init__(self, *args, **kwargs):
        super(BaseForm, self).__init__(*args, **kwargs)
        read_only(self.id)
        read_only(self.created_at)
        read_only(self.updated_at)
        read_only(self.created_by)
        read_only(self.updated_by)


class DataSearchForm(FlaskForm):
    per_page_choices = [(10, 10), (20, 20), (30, 30), (50, 50), (100, 100)]

    per_page = SelectField("Column", choices=per_page_choices, default=10)
    columns = SelectField("Column", choices=[], default=[("", "- Select Column -")])
    param_string = StringField("Param")

    def __init__(self, searchable_column_choices=None, *args, **kwargs):
        super(DataSearchForm, self).__init__(*args, **kwargs)
        self.columns.choices = searchable_column_choices


# def base_form(x):
#     if x is True:
#         _base_form = BasicForm
#     else:
#         _base_form = FlaskForm
#     return _base_form

def base_form(x):
    return BasicForm if x is True else FlaskForm

BaseForm = base_form(False)
