# -*- coding: utf-8 -*-
"""
arasCore/lib/installer.py
=========================
App Installer service.

Handles:
- Creating folder structure for a newly installed app
- Generating YAML/JSON template files (downloadable)
- Parsing uploaded YAML/JSON → AppManagerApp + AppManagerTable + AppManagerColumn
- Scaffold Python files (models.py, forms.py, views.py) — for code-based apps

Folder structure created per installed app:
    apps/{app_name}/
        templates/{app_name}/
        static/{app_name}/
            css/
            js/
            img/
        uploads/{app_name}/
"""
import os
import io
import yaml
import json
import logging
import textwrap

logger = logging.getLogger(__name__)

# ── Folder management ─────────────────────────────────────────────────────────

def get_apps_root(flask_app):
    # flask_app.root_path is arasCore/ — go up one level to project root, then into aras/
    project_root = os.path.dirname(flask_app.root_path)
    return os.path.join(project_root, "aras")


def create_app_folders(flask_app, app_name: str) -> dict:
    """
    Create the standard folder structure for an installed app under aras/app_{name}/.
    Returns dict of created paths.
    """
    module_name = f"app_{app_name}" if not app_name.startswith("app_") else app_name
    base = os.path.join(get_apps_root(flask_app), module_name)

    dirs = [
        base,
        os.path.join(base, "templates", app_name),
        os.path.join(base, "static", app_name, "css"),
        os.path.join(base, "static", app_name, "js"),
        os.path.join(base, "static", app_name, "img"),
        os.path.join(base, "uploads"),
    ]

    created = []
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        created.append(d)
        logger.info(f"[installer] folder: {d}")

    gitkeep = os.path.join(base, "uploads", ".gitkeep")
    if not os.path.exists(gitkeep):
        open(gitkeep, "w").close()

    return {"base": base, "dirs": created}


def remove_app_folders(flask_app, app_name: str):
    """Remove the app folder (use with caution)."""
    import shutil
    module_name = f"app_{app_name}" if not app_name.startswith("app_") else app_name
    base = os.path.join(get_apps_root(flask_app), module_name)
    if os.path.exists(base):
        shutil.rmtree(base)
        logger.info(f"[installer] removed: {base}")


# ── YAML template generation ──────────────────────────────────────────────────

_YAML_TEMPLATE = """\
# Aras App Definition — YAML format
# Upload this file in App Manager → Install App to create the app automatically.
# All fields are optional unless marked (required).

app:
  name: {name}                  # (required) slug, lowercase, no spaces — used as DB/URL prefix
  title: {title}                # (required) display title
  main_title: {main_title}      # sidebar / nav label
  url: {url}                    # URL prefix, e.g. /inventory
  endpoint: {endpoint}          # blueprint name (usually same as name)
  description: ""
  icon: fa-cubes
  is_active: true
  in_sidebar: true
  require_login: true
  api_enabled: true
  items_per_page: 20
  export_csv: false
  export_excel: false
  soft_delete: false
  audit_log: false

tables:
  - name: {table_name}          # (required) slug
    title: {table_title}        # (required) display title
    url_suffix: /{table_name}   # appended to app url
    menu_title: {table_title}
    menu_icon: fa-table
    show_in_menu: true
    menu_order: 0
    is_active: true
    allow_create: true
    allow_edit: true
    allow_delete: true
    detail_view: false
    search_enabled: true
    sort_field: id
    sort_direction: asc

    columns:
      - name: name              # (required) column slug
        label: Name             # (required) display label
        field_type: string      # string|text|integer|float|decimal|boolean|date|datetime|
                                # email|url|phone|select|file|image|json|uuid|relation
        required: false
        show_in_list: true
        show_in_form: true
        order: 0
        # optional:
        # placeholder: "Enter name..."
        # help_text: "Short description shown below field"
        # max_length: 200
        # unique: false
        # searchable: true
        # choices: "option1,option2,option3"   # for field_type: select
        # relation_system_table: auth_users     # for field_type: relation → system table
        # relation_display_col: username

      - name: description
        label: Description
        field_type: text
        required: false
        show_in_list: false
        show_in_form: true
        order: 1
"""

_JSON_TEMPLATE = {
    "app": {
        "name": "my_app",
        "title": "My App",
        "main_title": "My App",
        "url": "/my-app",
        "endpoint": "my_app",
        "description": "",
        "icon": "fa-cubes",
        "is_active": True,
        "in_sidebar": True,
        "require_login": True,
        "api_enabled": True,
        "items_per_page": 20,
        "export_csv": False,
        "export_excel": False,
        "soft_delete": False,
        "audit_log": False,
    },
    "tables": [
        {
            "name": "items",
            "title": "Items",
            "url_suffix": "/items",
            "menu_title": "Items",
            "menu_icon": "fa-table",
            "show_in_menu": True,
            "menu_order": 0,
            "is_active": True,
            "allow_create": True,
            "allow_edit": True,
            "allow_delete": True,
            "detail_view": False,
            "search_enabled": True,
            "sort_field": "id",
            "sort_direction": "asc",
            "columns": [
                {
                    "name": "name",
                    "label": "Name",
                    "field_type": "string",
                    "required": False,
                    "show_in_list": True,
                    "show_in_form": True,
                    "order": 0,
                },
                {
                    "name": "description",
                    "label": "Description",
                    "field_type": "text",
                    "required": False,
                    "show_in_list": False,
                    "show_in_form": True,
                    "order": 1,
                },
            ],
        }
    ],
}


def generate_yaml_template(app_name="my_app", app_title="My App",
                           table_name="items", table_title="Items") -> bytes:
    content = _YAML_TEMPLATE.format(
        name=app_name,
        title=app_title,
        main_title=app_title,
        url=f"/{app_name.replace('_', '-')}",
        endpoint=app_name,
        table_name=table_name,
        table_title=table_title,
    )
    return content.encode("utf-8")


def generate_json_template() -> bytes:
    return json.dumps(_JSON_TEMPLATE, indent=2).encode("utf-8")


# ── YAML/JSON parser → DB records ─────────────────────────────────────────────

def parse_app_definition(data: dict) -> dict:
    """
    Validate and normalize a parsed YAML/JSON app definition.
    Returns cleaned dict ready to pass into install_from_definition().
    Raises ValueError on missing required fields.
    """
    app_data = data.get("app") or data.get("App") or {}
    tables_data = data.get("tables") or data.get("Tables") or []

    required_app = ["name", "title"]
    for f in required_app:
        if not app_data.get(f):
            raise ValueError(f"Missing required app field: '{f}'")

    app_name = app_data["name"].strip().lower().replace(" ", "_").replace("-", "_")
    app_url  = app_data.get("url") or f"/{app_name.replace('_', '-')}"

    parsed_tables = []
    for tbl in tables_data:
        tname = (tbl.get("name") or "").strip().lower().replace(" ", "_")
        ttitle = tbl.get("title") or tname.replace("_", " ").title()
        if not tname:
            raise ValueError("Each table must have a 'name'.")

        columns = []
        for col in (tbl.get("columns") or []):
            cname = (col.get("name") or "").strip().lower().replace(" ", "_")
            clabel = col.get("label") or cname.replace("_", " ").title()
            if not cname:
                continue
            columns.append({
                "name":                  cname,
                "label":                 clabel,
                "field_type":            col.get("field_type", "string"),
                "required":              bool(col.get("required", False)),
                "order":                 int(col.get("order", 0)),
                "show_in_list":          bool(col.get("show_in_list", True)),
                "show_in_form":          bool(col.get("show_in_form", True)),
                "readonly":              bool(col.get("readonly", False)),
                "unique":                bool(col.get("unique", False)),
                "searchable":            bool(col.get("searchable", False)),
                "placeholder":           col.get("placeholder"),
                "help_text":             col.get("help_text"),
                "default_value":         col.get("default_value"),
                "max_length":            col.get("max_length"),
                "min_value":             col.get("min_value"),
                "max_value":             col.get("max_value"),
                "choices":               col.get("choices"),
                "relation_system_table": col.get("relation_system_table"),
                "relation_display_col":  col.get("relation_display_col"),
                "cascade_delete":        bool(col.get("cascade_delete", False)),
            })

        parsed_tables.append({
            "name":           tname,
            "title":          ttitle,
            "url_suffix":     tbl.get("url_suffix") or f"/{tname}",
            "menu_title":     tbl.get("menu_title") or ttitle,
            "menu_icon":      tbl.get("menu_icon", "fa-table"),
            "show_in_menu":   bool(tbl.get("show_in_menu", True)),
            "menu_order":     int(tbl.get("menu_order", 0)),
            "is_active":      bool(tbl.get("is_active", True)),
            "allow_create":   bool(tbl.get("allow_create", True)),
            "allow_edit":     bool(tbl.get("allow_edit", True)),
            "allow_delete":   bool(tbl.get("allow_delete", True)),
            "detail_view":    bool(tbl.get("detail_view", False)),
            "search_enabled": bool(tbl.get("search_enabled", True)),
            "sort_field":     tbl.get("sort_field"),
            "sort_direction": tbl.get("sort_direction", "asc"),
            "list_columns":   tbl.get("list_columns"),
            "parent_name":    tbl.get("parent_name"),  # resolved later
            "columns":        columns,
        })

    return {
        "app": {
            "name":          app_name,
            "title":         app_data.get("title", app_name.replace("_", " ").title()),
            "main_title":    app_data.get("main_title") or app_data.get("title", app_name),
            "url":           app_url,
            "endpoint":      app_data.get("endpoint") or app_name,
            "description":   app_data.get("description"),
            "icon":          app_data.get("icon", "fa-cubes"),
            "is_active":     bool(app_data.get("is_active", True)),
            "in_sidebar":    bool(app_data.get("in_sidebar", True)),
            "require_login": bool(app_data.get("require_login", True)),
            "api_enabled":   bool(app_data.get("api_enabled", True)),
            "items_per_page": int(app_data.get("items_per_page", 20)),
            "export_csv":    bool(app_data.get("export_csv", False)),
            "export_excel":  bool(app_data.get("export_excel", False)),
            "soft_delete":   bool(app_data.get("soft_delete", False)),
            "audit_log":     bool(app_data.get("audit_log", False)),
            "menu_order":    int(app_data.get("menu_order", 0)),
            "color_theme":   app_data.get("color_theme"),
        },
        "tables": parsed_tables,
    }


def install_from_definition(definition: dict, db, flask_app=None) -> "AppManagerApp":
    """
    Create AppManagerApp + AppManagerTable + AppManagerColumn from a parsed definition.
    Also creates folder structure if flask_app is provided.
    Returns the AppManagerApp instance (not yet activated).
    """
    from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable, AppManagerColumn

    app_data   = definition["app"]
    tables_data = definition["tables"]

    # Check for existing app
    existing = AppManagerApp.query.filter_by(name=app_data["name"]).first()
    if existing:
        raise ValueError(f"App '{app_data['name']}' already exists.")

    app_obj = AppManagerApp(**{k: v for k, v in app_data.items()})
    app_obj.is_active = False  # not active until explicitly activated
    db.session.add(app_obj)
    db.session.flush()  # get id

    # Build table name→id map for parent resolution
    tbl_name_map = {}

    for tbl_data in tables_data:
        parent_name = tbl_data.pop("parent_name", None)
        columns     = tbl_data.pop("columns", [])

        tbl = AppManagerTable(app_id=app_obj.id, **tbl_data)
        db.session.add(tbl)
        db.session.flush()

        tbl_name_map[tbl_data["name"]] = tbl

        for col_data in columns:
            col = AppManagerColumn(table_id=tbl.id, **col_data)
            db.session.add(col)

    # Resolve parent_table_id (second pass — simple approach)
    for tbl_data, tbl_obj in zip(tables_data, tbl_name_map.values()):
        pass  # parent resolution can be added when needed

    db.session.commit()

    if flask_app:
        try:
            create_app_folders(flask_app, app_data["name"])
        except Exception as e:
            logger.warning(f"[installer] folder creation failed: {e}")

    logger.info(f"[installer] Installed app '{app_data['name']}' with {len(tables_data)} table(s).")
    return app_obj


def load_definition_from_file(file_storage) -> dict:
    """
    Parse an uploaded FileStorage (YAML or JSON) into a definition dict.
    Routes through AppDefinitionMiddleware for normalization.
    Raises ValueError on parse error.
    """
    from arasCore.lib.middleware import AppDefinitionMiddleware
    return AppDefinitionMiddleware.from_file(file_storage)


# ── Python scaffold generator (for code-based apps) ──────────────────────────

def scaffold_python_app(app_name: str, tables: list) -> dict:
    """
    Generate Python file content for a code-based app.
    Returns dict: {filename: content_str}
    Tables format: [{"name": "products", "columns": [{"name": "title", "type": "String(200)"}]}]
    """
    files = {}

    # models.py
    model_lines = [
        "from datetime import datetime",
        "from arasCore.lib.extensions import db",
        "",
    ]
    for tbl in tables:
        class_name = tbl["name"].replace("_", " ").title().replace(" ", "")
        table_name = f"{app_name}_{tbl['name']}"
        model_lines += [
            f"class {class_name}(db.Model):",
            f'    __tablename__ = "{table_name}"',
            "    id         = db.Column(db.Integer, primary_key=True)",
            "    created_at = db.Column(db.DateTime, default=datetime.utcnow)",
        ]
        for col in tbl.get("columns", []):
            sa_type = _python_type(col.get("type", "string"))
            model_lines.append(f"    {col['name']} = db.Column({sa_type})")
        model_lines += ["", ""]

    files["models.py"] = "\n".join(model_lines)

    # forms.py
    form_lines = [
        "from flask_wtf import FlaskForm",
        "from wtforms import StringField, TextAreaField, IntegerField, BooleanField, DateField",
        "from wtforms.validators import DataRequired, Optional",
        "",
    ]
    for tbl in tables:
        class_name = tbl["name"].replace("_", " ").title().replace(" ", "")
        form_lines += [
            f"class {class_name}Form(FlaskForm):",
        ]
        for col in tbl.get("columns", []):
            wtf_field = _wtf_field(col.get("type", "string"))
            form_lines.append(
                f'    {col["name"]} = {wtf_field}("{col["name"].replace("_", " ").title()}", validators=[Optional()])'
            )
        if not tbl.get("columns"):
            form_lines.append("    pass")
        form_lines += ["", ""]

    files["forms.py"] = "\n".join(form_lines)

    # manifest.py scaffold — pakai AppHelper pattern
    model_names  = ", ".join(t["name"].replace("_", " ").title().replace(" ", "") for t in tables)
    resource_defs = "\n".join(
        f'        ResourceDef("{t["name"].replace("_", "-")}", '
        f'{t["name"].replace("_", " ").title().replace(" ", "")}, admin_list=True),'
        for t in tables
    )
    view_lines = textwrap.dedent(f"""\
        from arasCore.lib.app_helper import AppHelper, ResourceDef
        from .models import {model_names}

        helper = AppHelper(
            name="{app_name}",
            title="{app_name.replace("_", " ").title()}",
            resources=[
        {resource_defs}
            ],
        )
    """)
    files["manifest.py"] = view_lines
    files["views.py"] = "# Views tidak diperlukan — gunakan manifest.py + AppHelper.\n"

    # __init__.py
    files["__init__.py"] = ""

    return files


def _python_type(field_type: str) -> str:
    MAP = {
        "string": "db.String(200)",
        "text":   "db.Text",
        "integer": "db.Integer",
        "float":  "db.Float",
        "boolean": "db.Boolean, default=False",
        "date":   "db.Date",
        "datetime": "db.DateTime",
        "email":  "db.String(200)",
        "url":    "db.String(500)",
    }
    return MAP.get(field_type, "db.String(200)")


def _wtf_field(field_type: str) -> str:
    MAP = {
        "text":    "TextAreaField",
        "integer": "IntegerField",
        "boolean": "BooleanField",
        "date":    "DateField",
    }
    return MAP.get(field_type, "StringField")
