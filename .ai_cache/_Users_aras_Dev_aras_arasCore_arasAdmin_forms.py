# -*- coding: utf-8 -*-
"""arasCore/arasAdmin/forms.py — Admin forms."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, BooleanField, SelectField, IntegerField, PasswordField
from wtforms.validators import DataRequired, Length, Optional, Email, EqualTo


class CreateUserForm(FlaskForm):
    username  = StringField("Username", validators=[DataRequired(), Length(3, 64)])
    email     = StringField("Email", validators=[DataRequired(), Email()])
    password  = PasswordField("Password", validators=[DataRequired(), Length(6, 128)])
    password2 = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    is_admin  = BooleanField("Grant admin access")
    submit    = SubmitField("Create User")


ICON_CHOICES = [
    ("fa-cubes",         "Cubes"),
    ("fa-table",         "Table"),
    ("fa-list",          "List"),
    ("fa-file-text",     "Document"),
    ("fa-users",         "Users"),
    ("fa-shopping-cart", "Cart"),
    ("fa-cog",           "Settings"),
    ("fa-tag",           "Tag"),
    ("fa-folder",        "Folder"),
    ("fa-bar-chart",     "Chart"),
    ("fa-map-marker",    "Location"),
    ("fa-money",         "Money"),
    ("fa-truck",         "Truck"),
    ("fa-building",      "Building"),
    ("fa-inbox",         "Inbox"),
]

FIELD_TYPE_CHOICES = [
    ("string",   "String (varchar)"),
    ("text",     "Text (long text)"),
    ("integer",  "Integer"),
    ("float",    "Float"),
    ("decimal",  "Decimal (10,2)"),
    ("boolean",  "Boolean"),
    ("date",     "Date"),
    ("datetime", "DateTime"),
    ("email",    "Email"),
    ("url",      "URL"),
    ("phone",    "Phone"),
    ("select",   "Select (dropdown)"),
    ("file",     "File upload"),
    ("image",    "Image upload"),
    ("json",     "JSON"),
    ("uuid",     "UUID"),
    ("relation", "Relation (FK)"),
]


# class MessageForm(FlaskForm):
#     message = TextAreaField(
#         "Message", validators=[DataRequired(), Length(min=1, max=140)]
#     )
#     submit = SubmitField("Send")


# class PostForm(FlaskForm):
#     post = TextAreaField("Say something", validators=[DataRequired()])
#     submit = SubmitField("Post")


class AppManagerAppForm(FlaskForm):
    name       = StringField("Name (slug)", validators=[DataRequired(), Length(max=100)])
    title      = StringField("Title", validators=[DataRequired(), Length(max=200)])
    main_title = StringField("Main Title (sidebar label)", validators=[DataRequired(), Length(max=200)])
    url        = StringField("URL prefix (e.g. /notes)", validators=[DataRequired(), Length(max=200)])
    description   = StringField("Description", validators=[Optional(), Length(max=500)])
    icon          = SelectField("Icon", choices=ICON_CHOICES, default="fa-cubes")
    color_theme   = StringField("Color Theme (hex)", validators=[Optional(), Length(max=20)],
                                description="e.g. #3498db")
    is_active     = BooleanField("Active")
    in_sidebar    = BooleanField("Show in sidebar")
    require_login = BooleanField("Require login", default=True)
    api_enabled   = BooleanField("Enable REST API", default=True)
    items_per_page = IntegerField("Items per page", validators=[Optional()], default=20)
    export_csv    = BooleanField("Enable CSV export")
    export_excel  = BooleanField("Enable Excel export")
    soft_delete   = BooleanField("Soft delete (use deleted_at)")
    audit_log     = BooleanField("Audit log (track changes)")
    submit        = SubmitField("Save")


class AppManagerTableForm(FlaskForm):
    name         = StringField("Name (slug)", validators=[DataRequired(), Length(max=100)],
                               description="Lowercase, no spaces. Used as DB table suffix and URL.")
    title        = StringField("Title", validators=[DataRequired(), Length(max=200)])
    url_suffix   = StringField("URL suffix (e.g. /products)", validators=[DataRequired(), Length(max=200)])
    menu_title   = StringField("Menu Label", validators=[Optional(), Length(max=200)],
                               description="Defaults to Title if empty.")
    menu_icon    = SelectField("Menu Icon", choices=ICON_CHOICES, default="fa-table")
    show_in_menu = BooleanField("Show in sidebar menu", default=True)
    menu_order   = IntegerField("Menu Order", validators=[Optional()], default=0)
    parent_table_id = SelectField("Parent Table (child page)", coerce=int, validators=[Optional()])
    is_active    = BooleanField("Active", default=True)

    # Table-level settings
    search_enabled = BooleanField("Search bar", default=True)
    sort_field     = StringField("Default sort column", validators=[Optional(), Length(max=100)])
    sort_direction = SelectField("Sort direction", choices=[("asc","Ascending"),("desc","Descending")], default="asc")
    list_columns   = StringField("List columns (comma-separated)", validators=[Optional(), Length(max=500)],
                                 description="Leave blank to show all columns. Order matters.")
    per_page       = IntegerField("Rows per page", validators=[Optional()], default=20)
    allow_create   = BooleanField("Allow create", default=True)
    allow_edit     = BooleanField("Allow edit", default=True)
    allow_delete   = BooleanField("Allow delete", default=True)
    detail_view    = BooleanField("Enable detail/read-only view")

    submit         = SubmitField("Save Table")

    def __init__(self, app_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # populate parent_table choices dynamically
        choices = [(0, "— None (top-level) —")]
        if app_id:
            from arasCore.arasAdmin.models import AppManagerTable
            tables = AppManagerTable.query.filter_by(app_id=app_id).order_by(AppManagerTable.name).all()
            choices += [(t.id, t.title) for t in tables]
        self.parent_table_id.choices = choices


class AppManagerColumnForm(FlaskForm):
    name       = StringField("Column Name", validators=[DataRequired(), Length(max=100)],
                             description="DB column name, e.g. product_name")
    label      = StringField("Label (UI)", validators=[DataRequired(), Length(max=200)])
    field_type = SelectField("Type", choices=FIELD_TYPE_CHOICES, default="string")
    length     = IntegerField("Length (string only)", validators=[Optional()])
    required   = BooleanField("Required / NOT NULL")
    default_value = StringField("Default Value", validators=[Optional(), Length(max=200)])
    order      = IntegerField("Order", validators=[Optional()], default=0)

    # Display / UX
    placeholder  = StringField("Placeholder", validators=[Optional(), Length(max=200)])
    help_text    = StringField("Help Text", validators=[Optional(), Length(max=500)])
    show_in_list = BooleanField("Show in list view", default=True)
    show_in_form = BooleanField("Show in form", default=True)
    readonly     = BooleanField("Read-only")

    # Validation
    min_value  = StringField("Min Value", validators=[Optional(), Length(max=50)])
    max_value  = StringField("Max Value", validators=[Optional(), Length(max=50)])
    max_length = IntegerField("Max Length", validators=[Optional()])
    unique     = BooleanField("Unique constraint")
    searchable = BooleanField("Searchable")

    # Select choices
    choices = StringField("Choices (comma-separated)", validators=[Optional(), Length(max=2000)],
                          description="For select type, e.g. Active,Inactive,Pending")

    # Relation options
    relation_table_id     = SelectField("Target Table (in this app)", coerce=int,
                                        validators=[Optional()])
    relation_system_table = StringField("System Table (e.g. auth_users)",
                                        validators=[Optional(), Length(max=100)])
    relation_display_col  = StringField("Display Column", validators=[Optional(), Length(max=100)],
                                        description="Column shown in dropdown, e.g. name or username")
    cascade_delete        = BooleanField("Cascade Delete")
    submit = SubmitField("Add Column")

    def __init__(self, app_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [(0, "— Select target table —")]
        if app_id:
            from arasCore.arasAdmin.models import AppManagerTable
            tables = AppManagerTable.query.filter_by(app_id=app_id).order_by(AppManagerTable.name).all()
            choices += [(t.id, t.title) for t in tables]
        self.relation_table_id.choices = choices


# Kept for backward compat
class AppManagerFieldForm(AppManagerColumnForm):
    pass


class SearchForm(FlaskForm):
    q = StringField("Search", validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        from flask import request
        if "formdata" not in kwargs:
            kwargs["formdata"] = request.args
        if "meta" not in kwargs:
            kwargs["meta"] = {"csrf": False}
        super().__init__(*args, **kwargs)
