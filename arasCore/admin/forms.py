# -*- coding: utf-8 -*-
"""arasCore/admin/forms.py — Admin forms, declared in ArasGen lean style."""
from arasCore import ArasForm, Col, String, Text, Integer, Boolean, Select


# Static option lists used across forms
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

SORT_DIRECTION = [("asc", "Ascending"), ("desc", "Descending")]
SECTION_CHOICES = [("header", "Header"), ("content", "Content"),
                   ("extra", "Extra"), ("footer", "Footer")]


# ── User management ─────────────────────────────────────────────────────────

class CreateUserForm(ArasForm):
    username  = String(null=False, length=64)
    email     = Col(null=False)                          # → Email
    password  = Col(null=False, length=128)              # → Password
    password2 = Col(null=False, length=128, label="Confirm Password")
    is_admin  = Col(default=False, label="Grant admin access")


# ── App / Table / Column meta-forms (the GUI builder) ───────────────────────

class AppManagerAppForm(ArasForm):
    title          = String(null=False, length=200, label="Title (sidebar label)")
    url            = String(null=False, length=200, label="URL / Slug (e.g. erp)")
    description    = String(length=500)
    icon           = String(length=50, default="fa-cubes", label="Icon (e.g. fa-cubes)")
    color_theme    = String(length=20, label="Color Theme (hex)", help_text="e.g. #3498db")
    is_active      = Boolean(label="Active")
    in_sidebar     = Boolean(label="Show in sidebar")
    require_login  = Boolean(default=True, label="Require login")
    api_enabled    = Boolean(default=True, label="Enable REST API")
    items_per_page = Integer(default=20, label="Items per page")
    export_csv     = Boolean(label="Enable CSV export")
    export_excel   = Boolean(label="Enable Excel export")
    soft_delete    = Boolean(label="Soft delete (use deleted_at)")
    audit_log      = Boolean(label="Audit log (track changes)")


class AppManagerTableForm(ArasForm):
    name           = String(null=False, length=100, label="Name (slug)",
                            help_text="Lowercase, no spaces. Used as DB table suffix and URL.")
    title          = String(null=False, length=200)
    url_suffix     = String(null=False, length=200, label="URL suffix (e.g. /products)")
    menu_title     = String(length=200, label="Menu Label", help_text="Defaults to Title if empty.")
    menu_icon      = String(length=50, default="fa-table", label="Menu Icon (e.g. fa-table)")
    show_in_menu   = Boolean(default=True, label="Show in sidebar menu")
    menu_order     = Integer(default=0, label="Menu Order")
    parent_table_id = Select(label="Parent Table (child page)")
    is_active      = Boolean(default=True, label="Active")

    # Table-level settings
    search_enabled = Boolean(default=True, label="Search bar")
    sort_field     = String(length=100, label="Default sort column")
    sort_direction = Select(choices=SORT_DIRECTION, default="asc", label="Sort direction")
    list_columns    = String(length=500, label="List columns (comma-separated)",
                             help_text="Leave blank to show all columns. Order matters.")
    display_columns = String(length=200, label="Display columns when referenced (comma-separated)",
                             help_text="Fields shown when another table links to this one. "
                                       "E.g. 'code,name' → '1100 — Cash'. Leave blank to auto-detect.")
    per_page       = Integer(default=20, label="Rows per page")
    allow_create   = Boolean(default=True, label="Allow create")
    allow_edit     = Boolean(default=True, label="Allow edit")
    allow_delete   = Boolean(default=True, label="Allow delete")
    detail_view    = Boolean(label="Enable detail/read-only view")

    def __init__(self, app_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aras_fields["parent_table_id"].choices = _table_choices(app_id, "— None (top-level) —")


class AppManagerColumnForm(ArasForm):
    name          = String(null=False, length=100, label="Column Name",
                           help_text="DB column name, e.g. product_name")
    label         = String(null=False, length=200, label="Label (UI)")
    field_type    = Select(choices=FIELD_TYPE_CHOICES, default="string", label="Type")
    length        = Integer(label="Length (string only)")
    required      = Boolean(label="Required / NOT NULL")
    default_value = String(length=200, label="Default Value")
    order         = Integer(default=0)

    # Display / UX
    placeholder  = String(length=200)
    help_text    = String(length=500)
    show_in_list = Boolean(default=True, label="Show in list view")
    show_in_form = Boolean(default=True, label="Show in form")
    readonly     = Boolean(label="Read-only")

    # Validation
    min_value  = String(length=50, label="Min Value")
    max_value  = String(length=50, label="Max Value")
    max_length = Integer(label="Max Length")
    unique     = Boolean(label="Unique constraint")
    searchable = Boolean(label="Searchable")

    # Select choices
    choices = String(length=2000, label="Choices (comma-separated)",
                     help_text="For select type, e.g. Active,Inactive,Pending")

    # Relation options
    relation_table_id     = Select(label="Target Table (in this app)")
    relation_system_table = String(length=100, label="System Table (e.g. auth_users)")
    relation_display_col  = String(length=100, label="Display Column",
                                   help_text="Column shown in dropdown, e.g. name or username")
    cascade_delete        = Boolean(label="Cascade Delete")
    relation_filter       = String(length=500, label="Relation Filter",
                                   help_text="SQL WHERE snippet to filter combobox (e.g. is_group = 0)")
    default_section       = Select(choices=SECTION_CHOICES, default="content", label="Default Section")

    def __init__(self, app_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aras_fields["relation_table_id"].choices = _table_choices(app_id, "— Select target table —")


# Backward-compat alias
class AppManagerFieldForm(AppManagerColumnForm):
    pass


class SearchForm(ArasForm):
    q = String(null=False, label="Search")


# ── Helpers ─────────────────────────────────────────────────────────────────

def _table_choices(app_id, placeholder: str):
    """Build (id, title) choice list for table-picker selects."""
    out = [(0, placeholder)]
    if app_id:
        from arasCore.admin.models import AppManagerTable
        tables = (AppManagerTable.query
                  .filter_by(app_id=app_id)
                  .order_by(AppManagerTable.name)
                  .all())
        out.extend((t.id, t.title) for t in tables)
    return out
