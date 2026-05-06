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
    return os.path.join(project_root, "app")


def create_app_folders(flask_app, app_name: str) -> dict:
    """
    Create the standard folder structure for an installed app under aras/{name}/.
    Returns dict of created paths.
    """
    module_name = app_name[len("app_"):] if app_name.startswith("app_") else app_name
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
    module_name = app_name[len("app_"):] if app_name.startswith("app_") else app_name
    base = os.path.join(get_apps_root(flask_app), module_name)
    if os.path.exists(base):
        shutil.rmtree(base)
        logger.info(f"[installer] removed: {base}")

    # Remove RBAC permissions for the deleted app
    try:
        from arasCore.rbac import unseed_app_permissions
        from arasCore.lib.core.extensions import db
        unseed_app_permissions(app_name, db)
    except Exception as _re:
        logger.warning(f"[installer] RBAC unseed failed for {app_name}: {_re}")


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
    from arasCore.admin.models import AppManagerApp, AppManagerTable, AppManagerColumn

    app_data   = definition["app"]
    tables_data = definition["tables"]

    # Check for existing app
    _slug = app_data.get("url", app_data.get("name", "")).strip().strip("/")
    existing = AppManagerApp.query.filter_by(url=_slug).first()
    if existing:
        raise ValueError(f"App '{_slug}' already exists.")

    _allowed = {"url", "title", "icon", "description", "color_theme", "in_sidebar",
                "require_login", "api_enabled", "items_per_page", "export_csv",
                "export_excel", "soft_delete", "audit_log", "menu_order"}
    app_obj = AppManagerApp(**{k: v for k, v in app_data.items() if k in _allowed})
    app_obj.url = _slug
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
            paths = create_app_folders(flask_app, app_data["name"])
            base  = paths["base"]
            scaffold = scaffold_python_app(
                app_data["name"],
                [{"name": t["name"], "columns": [{"name": c["name"], "type": c["field_type"]} for c in t["columns"]]} for t in tables_data],
            )
            for fname, content in scaffold.items():
                fpath = os.path.join(base, fname)
                if not os.path.exists(fpath):
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(content)
                    logger.info(f"[installer] scaffold: {fpath}")
        except Exception as e:
            logger.warning(f"[installer] folder/scaffold creation failed: {e}")

    # Seed RBAC permissions for the new app's tables
    try:
        from arasCore.rbac import seed_app_permissions
        resource_slugs = [t.get("name") for t in tables_data if t.get("name")]
        if resource_slugs:
            seed_app_permissions(app_data["name"], resource_slugs, db)
    except Exception as _re:
        logger.warning(f"[installer] RBAC seed failed for {app_data['name']}: {_re}")

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
        "from arasCore.lib.core.extensions import db",
        "from arasCore.lib.core.base_model import ArasModel",
        "",
    ]
    for tbl in tables:
        class_name = tbl["name"].replace("_", " ").title().replace(" ", "")
        table_name = f"{app_name}_{tbl['name']}"
        model_lines += [
            f"class {class_name}(ArasModel):",
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
        # "from flask_wtf import FlaskForm",
        # "from wtforms import StringField, TextAreaField, IntegerField, BooleanField, DateField",
        # "from wtforms.validators import DataRequired, Optional",
        # "",
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
        from arasCore.lib.services.app_helper import AppHelper, ResourceDef
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


# ── SA model introspection helpers ───────────────────────────────────────────

_SYSTEM_COLS = {"id", "created_at", "updated_at", "deleted_at", "created_by_id", "updated_by_id"}


def _sa_type_to_field_type(sa_type) -> str:
    import sqlalchemy as _sa
    if isinstance(sa_type, (_sa.Integer, _sa.BigInteger, _sa.SmallInteger)):
        return "integer"
    if isinstance(sa_type, (_sa.Numeric, _sa.Float)):
        return "decimal" if isinstance(sa_type, _sa.Numeric) else "float"
    if isinstance(sa_type, _sa.Boolean):
        return "boolean"
    if isinstance(sa_type, _sa.Date):
        return "date"
    if isinstance(sa_type, _sa.DateTime):
        return "datetime"
    if isinstance(sa_type, _sa.Text):
        return "text"
    if isinstance(sa_type, _sa.JSON):
        return "json"
    return "string"


def _sa_col_label(name: str) -> str:
    """'from_user_id' → 'From User', 'like_count' → 'Like Count'"""
    n = name[:-3] if name.endswith("_id") else name
    return n.replace("_", " ").title()


def _sa_column_to_def(col, order: int) -> dict:
    """Convert a SQLAlchemy Column object → mgr_column creation dict."""
    # Relation detection
    if col.foreign_keys:
        fk = next(iter(col.foreign_keys))
        target_table = fk.column.table.name if hasattr(fk, "column") else str(fk.target_fullname).split(".")[0]
        rel_sys = target_table if target_table == "auth_users" else None
        rel_display = "username" if target_table == "auth_users" else None
        return {
            "name":                 col.name,
            "label":                _sa_col_label(col.name),
            "field_type":           "relation",
            "required":             not col.nullable,
            "order":                order,
            "show_in_list":         True,
            "show_in_form":         True,
            "relation_system_table": rel_sys,
            "relation_display_col": rel_display,
        }

    field_type = _sa_type_to_field_type(col.type)
    show_in_form = col.name not in _SYSTEM_COLS

    return {
        "name":         col.name,
        "label":        _sa_col_label(col.name),
        "field_type":   field_type,
        "required":     not col.nullable and col.default is None and not col.server_default,
        "order":        order,
        "show_in_list": col.name not in _SYSTEM_COLS,
        "show_in_form": show_in_form,
    }


def sync_helper_to_db(helper, db, flask_app=None) -> "object":
    """
    Sync an AppHelper (code-based app) into mgr_app / mgr_table / mgr_column.

    Idempotent: existing records are skipped; only new tables/columns are inserted.
    Use for initial install AND re-sync after adding columns to a model.

    Returns the AppManagerApp instance.
    """
    from arasCore.admin.models import AppManagerApp, AppManagerTable, AppManagerColumn

    # ── 1. mgr_app upsert ────────────────────────────────────────────────────
    _slug = (getattr(helper, "admin_slug", None) or helper.name).strip("/")
    app_rec = AppManagerApp.query.filter_by(url=_slug).first()
    if not app_rec:
        app_rec = AppManagerApp(
            url=_slug,
            title=helper.title,
            icon=helper.admin_icon,
            menu_order=helper.admin_order,
            is_active=False,
        )
        db.session.add(app_rec)
        db.session.flush()
        logger.info(f"[sync] created mgr_app: {helper.name}")
    else:
        logger.info(f"[sync] mgr_app already exists: {helper.name}")

    stats = {"tables_new": 0, "tables_existing": 0, "cols_new": 0, "cols_skipped": 0, "tables_removed": 0}

    # Build set of canonical names from the current manifest
    def _canonical_names(h):
        names = {"_settings"}
        for grp in (h.menu_groups or []):
            names.add(f"_group_{grp.title.lower().replace(' ', '_')}")
            for r in grp.resources:
                names.add(r.name)
        for r in (h.resources or []):
            names.add(r.name)
        return names

    canonical = _canonical_names(helper)
    # Remove stale mgr_table rows that are no longer in the manifest
    stale = AppManagerTable.query.filter_by(app_id=app_rec.id).filter(
        ~AppManagerTable.name.in_(canonical)
    ).all()
    for s in stale:
        db.session.delete(s)
        stats["tables_removed"] += 1
        logger.info(f"[sync]   removed stale table: {s.name}")
    if stale:
        db.session.flush()

    def _sync_resource(res, parent_id, order):
        """Upsert one ResourceDef into mgr_table + sync columns. Returns the record."""
        if not res.model:
            # URL-only ResourceDef — create a link tile pointing to res.url
            if res.url and res.admin_list:
                suffix = res.url.replace("/admin" + app_rec.url_prefix, "").rstrip("/") or "/"
                link_rec = AppManagerTable.query.filter_by(app_id=app_rec.id, name=res.name).first()
                if not link_rec:
                    link_rec = AppManagerTable(
                        app_id=app_rec.id,
                        name=res.name,
                        title=res.get_menu_title(),
                        url_suffix=suffix,
                        db_table_name=None,
                        menu_title=res.menu_title or res.get_menu_title(),
                        menu_icon=res.menu_icon,
                        show_in_menu=True,
                        menu_order=order,
                        parent_table_id=parent_id,
                        page_type="link",
                    )
                    db.session.add(link_rec)
                    db.session.flush()
                    stats["tables_new"] += 1
                    logger.info(f"[sync]   link tile: {res.name} -> {suffix}")
                else:
                    link_rec.parent_table_id = parent_id
                    link_rec.menu_order      = order
                    link_rec.url_suffix      = suffix
                    stats["tables_existing"] += 1
            return None
        tbl_name = res.model.__tablename__
        tbl_rec = AppManagerTable.query.filter_by(app_id=app_rec.id, name=res.name).first()
        if not tbl_rec:
            tbl_rec = AppManagerTable(
                app_id=app_rec.id,
                name=res.name,
                title=res.get_menu_title(),
                url_suffix=f"/{res.name}",
                db_table_name=tbl_name,
                menu_title=res.menu_title or res.get_menu_title(),
                menu_icon=res.menu_icon,
                show_in_menu=res.admin_list,
                menu_order=order,
                parent_table_id=parent_id,
                allow_create=not res.readonly,
                allow_edit=not res.readonly,
                allow_delete=not res.readonly,
            )
            db.session.add(tbl_rec)
            db.session.flush()
            stats["tables_new"] += 1
            logger.info(f"[sync]   table: {res.name} ({tbl_name})")
        else:
            # Always update structural fields so re-sync fixes parent/order/visibility
            tbl_rec.parent_table_id = parent_id
            tbl_rec.menu_order      = order
            tbl_rec.show_in_menu    = res.admin_list
            stats["tables_existing"] += 1

        existing_col_names = {c.name for c in AppManagerColumn.query.filter_by(table_id=tbl_rec.id).all()}
        for col_order, col in enumerate(res.model.__table__.columns):
            if col.primary_key or col.name in existing_col_names:
                stats["cols_skipped"] += 1
                continue
            col_def = _sa_column_to_def(col, col_order)
            db.session.add(AppManagerColumn(table_id=tbl_rec.id, **col_def))
            stats["cols_new"] += 1
        return tbl_rec

    # ── 2. Sync resources — grouped (MenuGroup) or flat ──────────────────────
    num_groups = len(helper.menu_groups) if helper.menu_groups else 0
    if helper.menu_groups:
        for grp_order, grp in enumerate(sorted(helper.menu_groups, key=lambda g: g.order)):
            grp_name = f"_group_{grp.title.lower().replace(' ', '_')}"
            grp_slug = grp.title.lower().replace(" ", "-")
            grp_rec = AppManagerTable.query.filter_by(app_id=app_rec.id, name=grp_name).first()
            if not grp_rec:
                grp_rec = AppManagerTable(
                    app_id=app_rec.id,
                    name=grp_name,
                    title=grp.title,
                    url_suffix=f"/{grp_slug}",
                    db_table_name=None,
                    menu_title=grp.title,
                    menu_icon=grp.icon,
                    show_in_menu=True,
                    menu_order=grp_order,
                    parent_table_id=None,
                    page_type="group",
                )
                db.session.add(grp_rec)
                db.session.flush()
                stats["tables_new"] += 1
                logger.info(f"[sync]   group: {grp.title}")
            else:
                grp_rec.title      = grp.title
                grp_rec.menu_title = grp.title
                grp_rec.menu_icon  = grp.icon
                grp_rec.menu_order = grp_order

            for res_order, res in enumerate(grp.resources):
                _sync_resource(res, grp_rec.id, res_order)
    else:
        for res_order, res in enumerate(helper.resources):
            _sync_resource(res, None, res_order)

    # ── 3. Settings link — skip if a MenuGroup named "Settings" already covers it
    has_settings_group = helper.menu_groups and any(
        g.title.lower() == "settings" for g in helper.menu_groups
    )
    if not has_settings_group:
        settings_rec = AppManagerTable.query.filter_by(app_id=app_rec.id, name="_settings").first()
        if not settings_rec:
            settings_rec = AppManagerTable(
                app_id=app_rec.id,
                name="_settings",
                title="Settings",
                url_suffix="/settings",
                db_table_name=None,
                menu_title="Settings",
                menu_icon="fa-cog",
                show_in_menu=True,
                menu_order=num_groups + 100,
                parent_table_id=None,
                page_type="settings",
            )
            db.session.add(settings_rec)
            db.session.flush()
            stats["tables_new"] += 1
            logger.info(f"[sync]   settings link added")

    db.session.commit()
    logger.info(f"[sync] done: {stats}")

    # Seed RBAC permissions for all resources in this code-based app
    try:
        from arasCore.rbac import seed_app_permissions_from_helper
        seed_app_permissions_from_helper(helper, db)
    except Exception as _re:
        logger.warning(f"[sync] RBAC seed failed for {helper.name}: {_re}")

    return app_rec, stats
