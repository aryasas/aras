# -*- coding: utf-8 -*-
"""
arasCore/arasAdmin/models.py
Admin + Builder models.
"""
from datetime import datetime
from time import time
import json
from arasCore.lib.extensions import db
from arasCore.lib.base_model import ArasModel


# ── App Manager ───────────────────────────────────────────────────────────────

class AppManagerApp(ArasModel):
    """
    Defines a dynamically-built application.
    Replaces physical app_* folders — everything stored in DB.
    """
    __tablename__ = "mgr_app"

    url        = db.Column(db.String(200), unique=True, nullable=False)
    title      = db.Column(db.String(200), nullable=False)
    in_sidebar = db.Column(db.Boolean, default=True, nullable=False)

    icon       = db.Column(db.String(50),  default="fa-cubes")
    menu_order = db.Column(db.Integer, default=0)

    # App-level settings
    description    = db.Column(db.Text, nullable=True)
    color_theme    = db.Column(db.String(20), nullable=True)
    require_login  = db.Column(db.Boolean, default=True)
    api_enabled    = db.Column(db.Boolean, default=True)
    items_per_page = db.Column(db.Integer, default=20)
    export_csv     = db.Column(db.Boolean, default=False)
    export_excel   = db.Column(db.Boolean, default=False)
    soft_delete    = db.Column(db.Boolean, default=False)
    audit_log      = db.Column(db.Boolean, default=False)

    tables = db.relationship(
        "AppManagerTable",
        backref="app",
        lazy="dynamic",
        cascade="all, delete-orphan",
        foreign_keys="AppManagerTable.app_id",
    )
    # kept for backward compat
    fields = db.relationship(
        "AppManagerField",
        backref="app",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    @property
    def slug(self) -> str:
        return (self.url or "").strip().strip("/")

    @property
    def url_prefix(self) -> str:
        return f"/{self.slug}"

    @property
    def endpoint(self) -> str:
        return self.slug

    def admin_url(self, table: "AppManagerTable" = None) -> str:
        """Return /admin/<slug>/ or /admin/<slug>/<table.url_suffix>/."""
        if table is None:
            return f"/admin{self.url_prefix}/"
        return f"/admin{table.get_full_url(self.url_prefix)}/"

    def get_tables(self):
        return self.tables.order_by(AppManagerTable.menu_order).all()

    def get_fields(self):
        return self.fields.order_by(AppManagerField.order).all()

    def to_dict(self):
        return {
            "id":         self.id,
            "url":        self.url,
            "title":      self.title,
            "is_active":  self.is_active,
            "in_sidebar": self.in_sidebar,
            "fields":     [f.to_dict() for f in self.get_fields()],
        }

    def __repr__(self):
        return f"<AppManagerApp {self.slug}>"


class AppManagerTable(ArasModel):
    """One table/page within an AppManagerApp."""
    __tablename__ = "mgr_table"

    app_id          = db.Column(db.Integer, db.ForeignKey("mgr_app.id"), nullable=False)
    parent_table_id = db.Column(db.Integer, db.ForeignKey("mgr_table.id"), nullable=True)

    name            = db.Column(db.String(100), nullable=False)
    title           = db.Column(db.String(200), nullable=False)
    url_suffix      = db.Column(db.String(200), nullable=False, default="")
    db_table_name   = db.Column(db.String(200), nullable=True)

    menu_title      = db.Column(db.String(200), nullable=True)
    menu_icon       = db.Column(db.String(50),  default="fa-table")
    show_in_menu    = db.Column(db.Boolean, default=True)
    menu_order      = db.Column(db.Integer, default=0)

    # Table-level settings
    search_enabled  = db.Column(db.Boolean, default=True)
    sort_field      = db.Column(db.String(100), nullable=True)
    sort_direction  = db.Column(db.String(4), default="asc")
    list_columns     = db.Column(db.Text, nullable=True)   # comma-separated column names for list view
    display_columns  = db.Column(db.String(200), nullable=True)  # CSV cols used when this table is a FK target, e.g. "code,name"
    per_page        = db.Column(db.Integer, default=20)
    allow_create    = db.Column(db.Boolean, default=True)
    allow_edit      = db.Column(db.Boolean, default=True)
    allow_delete    = db.Column(db.Boolean, default=True)
    detail_view     = db.Column(db.Boolean, default=False)

    # ── Page Type metadata (DocType-style) ────────────────────────────────────
    # page_type: "list" (default, standard CRUD list+form),
    #            "single" (one global record — like ERPNext "Single DocType"),
    #            "report" (read-only query result), "dashboard" (widget board).
    page_type       = db.Column(db.String(20),  default="list")
    description     = db.Column(db.String(500), nullable=True)
    icon            = db.Column(db.String(50),  nullable=True)   # alternative to menu_icon
    show_in_home    = db.Column(db.Boolean, default=True)        # tile on app home page

    # Document lifecycle
    is_submittable  = db.Column(db.Boolean, default=False)       # adds submit/cancel buttons
    track_changes   = db.Column(db.Boolean, default=False)

    # Naming: "auto" (id), "field:<name>" (use a field), "pattern" (use autoname_pattern)
    naming_rule      = db.Column(db.String(20),  default="auto")
    autoname_pattern = db.Column(db.String(100), nullable=True)  # e.g. "INV-.####"

    # Layout override — JSON describing sections/columns for the form view.
    # Example: {"sections": [{"title": "Main", "columns": [["name","email"], ["phone"]]}]}
    layout_json      = db.Column(db.Text, nullable=True)

    # RBAC: optional role slug required to access this table (overrides permission check)
    required_role_slug = db.Column(db.String(64), nullable=True)

    # Child table footer totals — CSV of numeric field names to sum, e.g. "qty,subtotal,amount"
    footer_totals_fields = db.Column(db.String(500), nullable=True)

    columns = db.relationship(
        "AppManagerColumn",
        backref="table",
        lazy="dynamic",
        cascade="all, delete-orphan",
        foreign_keys="AppManagerColumn.table_id",
    )
    children = db.relationship(
        "AppManagerTable",
        backref=db.backref("parent", remote_side="AppManagerTable.id"),
        lazy="dynamic",
        foreign_keys="AppManagerTable.parent_table_id",
    )

    @property
    def app_name(self):
        try:
            return self.app.slug
        except Exception:
            return ""

    def get_columns(self):
        return self.columns.order_by(AppManagerColumn.order).all()

    def get_db_table_name(self, app_name):
        # Use explicit override first; otherwise derive from app_name (hyphens → underscores)
        if self.db_table_name:
            return self.db_table_name
        safe = app_name.replace("-", "_")
        return f"{safe}_{self.name}"

    def get_full_url(self, app_url):
        return f"{app_url}{self.url_suffix}"

    @property
    def edit_url(self):
        return f"/admin/apps/{self.app_id}/tables/{self.id}/edit"

    def get_menu_title(self):
        return self.menu_title or self.title

    def to_dict(self):
        return {
            "id":              self.id,
            "app_id":          self.app_id,
            "parent_table_id": self.parent_table_id,
            "name":            self.name,
            "title":           self.title,
            "url_suffix":      self.url_suffix,
            "menu_title":      self.get_menu_title(),
            "menu_icon":       self.menu_icon,
            "show_in_menu":    self.show_in_menu,
            "menu_order":      self.menu_order,
            "is_active":       self.is_active,
        }

    def __repr__(self):
        return f"<AppManagerTable {self.name}>"


class AppManagerColumn(ArasModel):
    """A column/field within an AppManagerTable."""
    __tablename__ = "mgr_column"

    FIELD_TYPES = [
        "string", "text", "integer", "float", "decimal", "boolean",
        "date", "datetime", "email", "url", "phone", "select",
        "file", "image", "json", "uuid", "relation", "formula",
    ]

    table_id   = db.Column(db.Integer, db.ForeignKey("mgr_table.id"), nullable=False)
    name       = db.Column(db.String(100), nullable=False)
    label      = db.Column(db.String(200), nullable=False)
    field_type = db.Column(db.String(50),  nullable=False, default="string")
    length     = db.Column(db.Integer, nullable=True)
    required   = db.Column(db.Boolean, default=False)
    default_value  = db.Column(db.String(200), nullable=True)
    order      = db.Column(db.Integer, default=0)

    # Display / UX settings
    placeholder   = db.Column(db.String(200), nullable=True)
    help_text     = db.Column(db.String(500), nullable=True)
    show_in_list  = db.Column(db.Boolean, default=True)
    show_in_form  = db.Column(db.Boolean, default=True)
    readonly      = db.Column(db.Boolean, default=False)

    # Validation settings
    min_value  = db.Column(db.String(50), nullable=True)
    max_value  = db.Column(db.String(50), nullable=True)
    max_length = db.Column(db.Integer, nullable=True)
    unique     = db.Column(db.Boolean, default=False)
    searchable = db.Column(db.Boolean, default=False)

    # Formula / computed
    formula = db.Column(db.Text, nullable=True)   # Python expr e.g. "qty * unit_price"

    # Child table tab — if True and this field is a relation pointing to a child table,
    # the child records are auto-loaded into a dedicated tab on the parent form view
    view_in_tab = db.Column(db.Boolean, default=False)

    # Validation
    regex_pattern = db.Column(db.String(300), nullable=True)

    # Select / choices
    choices = db.Column(db.Text, nullable=True)  # comma-separated option values

    # Relation-specific
    relation_table_id     = db.Column(db.Integer, db.ForeignKey("mgr_table.id"), nullable=True)
    relation_system_table = db.Column(db.String(100), nullable=True)
    relation_display_col  = db.Column(db.String(100), nullable=True)
    cascade_delete        = db.Column(db.Boolean, default=False)

    relation_table = db.relationship(
        "AppManagerTable",
        foreign_keys=[relation_table_id],
        lazy="select",
    )

    def to_dict(self):
        return {
            "id":                    self.id,
            "table_id":              self.table_id,
            "name":                  self.name,
            "label":                 self.label,
            "field_type":            self.field_type,
            "length":                self.length,
            "required":              self.required,
            "default_value":         self.default_value,
            "order":                 self.order,
            "placeholder":           self.placeholder,
            "help_text":             self.help_text,
            "show_in_list":          self.show_in_list,
            "show_in_form":          self.show_in_form,
            "readonly":              self.readonly,
            "min_value":             self.min_value,
            "max_value":             self.max_value,
            "max_length":            self.max_length,
            "unique":                self.unique,
            "searchable":            self.searchable,
            "choices":               self.choices,
            "formula":               self.formula,
            "view_in_tab":           self.view_in_tab,
            "regex_pattern":         self.regex_pattern,
            "relation_table_id":     self.relation_table_id,
            "relation_system_table": self.relation_system_table,
            "relation_display_col":  self.relation_display_col,
            "cascade_delete":        self.cascade_delete,
        }

    def __repr__(self):
        return f"<AppManagerColumn {self.name}:{self.field_type}>"


class AppManagerPageAction(ArasModel):
    """Custom action button bound to a page type."""
    __tablename__ = "mgr_page_action"

    VISIBILITY = ("list", "form", "both")
    STYLES     = ("primary", "secondary", "success", "warning", "danger", "info", "light", "dark")

    table_id     = db.Column(db.Integer, db.ForeignKey("mgr_table.id"), nullable=False)
    name         = db.Column(db.String(100), nullable=False)     # slug, stable id
    label        = db.Column(db.String(200), nullable=False)     # button label
    icon         = db.Column(db.String(50),  nullable=True)      # e.g. fa-check
    handler_name = db.Column(db.String(200), nullable=False)     # key into action registry
    visibility   = db.Column(db.String(10),  default="form")     # list|form|both
    style        = db.Column(db.String(20),  default="secondary")
    confirm_msg  = db.Column(db.String(300), nullable=True)      # if set, UI asks to confirm
    order        = db.Column(db.Integer, default=0)

    table = db.relationship(
        "AppManagerTable",
        backref=db.backref("actions", lazy="dynamic", cascade="all, delete-orphan"),
        foreign_keys=[table_id],
    )

    def to_dict(self):
        return {
            "id": self.id, "table_id": self.table_id, "name": self.name,
            "label": self.label, "icon": self.icon, "handler_name": self.handler_name,
            "visibility": self.visibility, "style": self.style,
            "confirm_msg": self.confirm_msg, "order": self.order,
            "is_active": self.is_active,
        }

    def __repr__(self):
        return f"<AppManagerPageAction {self.name}>"


class AppManagerPageView(ArasModel):
    """Saved view (filter + sort + columns preset) for a page type."""
    __tablename__ = "mgr_page_view"

    table_id    = db.Column(db.Integer, db.ForeignKey("mgr_table.id"), nullable=False)
    name        = db.Column(db.String(100), nullable=False)
    label       = db.Column(db.String(200), nullable=False)
    owner_id    = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)
    is_default  = db.Column(db.Boolean, default=False)
    is_shared   = db.Column(db.Boolean, default=False)
    filter_json = db.Column(db.Text, nullable=True)
    sort_json   = db.Column(db.Text, nullable=True)
    columns_csv = db.Column(db.String(500), nullable=True)
    order       = db.Column(db.Integer, default=0)

    table = db.relationship(
        "AppManagerTable",
        backref=db.backref("saved_views", lazy="dynamic", cascade="all, delete-orphan"),
        foreign_keys=[table_id],
    )

    def __repr__(self):
        return f"<AppManagerPageView {self.name}>"


class AppManagerDashboard(ArasModel):
    """Dashboard widget per app. Can be user/role-scoped when builder is enabled."""
    __tablename__ = "mgr_dashboard"

    WIDGET_TYPES = ("count", "sum", "chart", "list", "html")

    app_id      = db.Column(db.Integer, db.ForeignKey("mgr_app.id"), nullable=False)
    name        = db.Column(db.String(100), nullable=False)
    label       = db.Column(db.String(200), nullable=False)
    widget_type = db.Column(db.String(20),  default="count")
    icon        = db.Column(db.String(50),  nullable=True)
    color       = db.Column(db.String(20),  default="primary")
    data_source = db.Column(db.String(200), nullable=False)
    config_json = db.Column(db.Text, nullable=True)
    link_url    = db.Column(db.String(300), nullable=True)
    width       = db.Column(db.Integer, default=3)
    order       = db.Column(db.Integer, default=0)
    # User/role scoping (NULL = shown to all users with app access)
    user_id     = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)
    role_id     = db.Column(db.Integer, db.ForeignKey("auth_roles.id"), nullable=True)
    # Layout position override (JSON: {row, col})
    layout_json = db.Column(db.Text, nullable=True)

    app = db.relationship(
        "AppManagerApp",
        backref=db.backref("dashboards", lazy="dynamic", cascade="all, delete-orphan"),
        foreign_keys=[app_id],
    )

    def __repr__(self):
        return f"<AppManagerDashboard {self.name}>"


class AppManagerSetting(ArasModel):
    """Per-app key/value settings. One row per (app_id, key)."""
    __tablename__ = "mgr_app_setting"

    id         = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (
        db.UniqueConstraint("app_id", "key", name="uq_mgr_app_setting_app_key"),
    )

    VALUE_TYPES = ("string", "text", "integer", "float", "boolean", "json")

    app_id     = db.Column(db.Integer, db.ForeignKey("mgr_app.id"), nullable=False)
    key        = db.Column(db.String(100), nullable=False)
    label      = db.Column(db.String(200), nullable=True)
    value      = db.Column(db.Text, nullable=True)
    value_type = db.Column(db.String(20), nullable=False, default="string")
    help_text  = db.Column(db.String(500), nullable=True)
    order      = db.Column(db.Integer, default=0)

    app = db.relationship(
        "AppManagerApp",
        backref=db.backref("settings", lazy="dynamic", cascade="all, delete-orphan"),
        foreign_keys=[app_id],
    )

    def get_value(self):
        v = self.value
        if v is None:
            return None
        vt = self.value_type or "string"
        try:
            if vt == "integer":
                return int(v)
            if vt == "float":
                return float(v)
            if vt == "boolean":
                return str(v).lower() in ("1", "true", "yes", "on")
            if vt == "json":
                return json.loads(v)
        except (ValueError, TypeError, json.JSONDecodeError):
            return v
        return v

    def set_value(self, raw):
        vt = self.value_type or "string"
        if raw is None:
            self.value = None
            return
        if vt == "json":
            self.value = raw if isinstance(raw, str) else json.dumps(raw)
        elif vt == "boolean":
            self.value = "true" if (raw is True or str(raw).lower() in ("1", "true", "yes", "on")) else "false"
        else:
            self.value = str(raw)

    def to_dict(self):
        return {
            "id": self.id, "app_id": self.app_id, "key": self.key,
            "label": self.label, "value": self.get_value(),
            "value_type": self.value_type, "help_text": self.help_text,
            "order": self.order,
        }

    def __repr__(self):
        return f"<AppManagerSetting {self.app_id}:{self.key}>"


# Keep for backward compat — routes/services may still reference this
class AppManagerField(ArasModel):
    """Deprecated — use AppManagerColumn via AppManagerTable instead."""
    __tablename__ = "mgr_field"

    app_id     = db.Column(db.Integer, db.ForeignKey("mgr_app.id"), nullable=False)
    name       = db.Column(db.String(100), nullable=False)
    label      = db.Column(db.String(200), nullable=False)
    field_type = db.Column(db.String(50),  nullable=False, default="string")
    required   = db.Column(db.Boolean, default=False)
    order      = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id, "app_id": self.app_id, "name": self.name,
            "label": self.label, "field_type": self.field_type,
            "required": self.required, "order": self.order,
        }

    def __repr__(self):
        return f"<AppManagerField {self.name}:{self.field_type}>"


# ── Menu Definition (DB-driven nav) ──────────────────────────────────────────

class MenuDefinition(ArasModel):
    """Top navbar menu entries, generated from active apps + roles."""
    __tablename__ = "mgr_menu"

    app_id     = db.Column(db.Integer, db.ForeignKey("mgr_app.id"), nullable=True)
    title      = db.Column(db.String(100), nullable=False)
    url        = db.Column(db.String(200))
    icon       = db.Column(db.String(50))
    order      = db.Column(db.Integer, default=0)
    role_slug  = db.Column(db.String(64), nullable=True)

    def __repr__(self):
        return f"<MenuDefinition {self.title}>"


# ── Messaging ─────────────────────────────────────────────────────────────────

# class Message(db.Model):
#     """Private messages between users."""
#     __tablename__ = "adm_message"

#     id           = db.Column(db.Integer, primary_key=True)
#     sender_id    = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
#     recipient_id = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
#     body         = db.Column(db.String(140), nullable=False)
#     timestamp    = db.Column(db.DateTime, index=True, default=datetime.utcnow)

#     sender    = db.relationship("User", foreign_keys=[sender_id],
#                                 backref=db.backref("messages_sent", lazy="dynamic"))
#     recipient = db.relationship("User", foreign_keys=[recipient_id],
#                                 backref=db.backref("messages_received", lazy="dynamic"))

#     def __repr__(self):
#         return f"<Message {self.body[:30]}>"


# ── Notifications ─────────────────────────────────────────────────────────────

class Notification(ArasModel):
    """User notifications (badge counts, alerts)."""
    __tablename__ = "adm_notification"

    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(128), index=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    timestamp    = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)
    category     = db.Column(db.String(128))

    user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("notifications", lazy="dynamic"))

    def get_data(self):
        return json.loads(str(self.payload_json))

    def __repr__(self):
        return f"<Notification {self.name}>"


# ── User Activity ─────────────────────────────────────────────────────────────

class UserActivity(ArasModel):
    """Audit log of user actions."""
    __tablename__ = "adm_user_activity"

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    name         = db.Column(db.String(128), index=True)
    module       = db.Column(db.String(128))
    payload_json = db.Column(db.Text)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id  = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)
    updated_by_id  = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)

    user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("activities", lazy="dynamic"))

    @property
    def edit_url(self):
        return f"/admin/users/{self.user_id}/"

    def get_data(self):
        return json.loads(str(self.payload_json)) if self.payload_json else {}

    def __repr__(self):
        return f"<UserActivity {self.name}>"


# ── Framework Audit Log ───────────────────────────────────────────────────────

class ArasCoreAuditLog(ArasModel):
    """
    Framework-level audit trail for tables with track_changes=True.
    Activated per-table via AppManagerTable.track_changes or model.__track_changes__ = True.
    """
    __tablename__ = "aras_audit_log"
    __table_args__ = (
        db.Index("idx_aras_audit", "model_name", "record_id"),
    )

    id          = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    ts          = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # noqa: DTZ
    user_id     = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)
    model_name  = db.Column(db.String(100), nullable=False)
    record_id   = db.Column(db.Integer, nullable=True)
    action      = db.Column(db.String(20), nullable=False)   # create / update / delete
    before_json = db.Column(db.JSON, nullable=True)
    after_json  = db.Column(db.JSON, nullable=True)
    ip          = db.Column(db.String(45), nullable=True)

    def __repr__(self):
        return f"<AuditLog {self.action} {self.model_name}#{self.record_id}>"


# ── Per-user list view preferences ───────────────────────────────────────────

class ListViewSetting(ArasModel):
    """Persists column visibility, page size, and view mode per user per doctype."""
    __tablename__ = "adm_list_view_setting"
    __table_args__ = (
        db.UniqueConstraint("user_id", "doctype", name="uq_adm_list_view"),
    )

    user_id      = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    doctype      = db.Column(db.String(120), nullable=False)
    columns_json = db.Column(db.Text, nullable=True)
    page_size    = db.Column(db.Integer, default=20, nullable=False)
    view_mode    = db.Column(db.String(10), default="list", nullable=False)
    show_totals  = db.Column(db.Boolean, default=False, nullable=False)


# ── Post ──────────────────────────────────────────────────────────────────────

# class Post(db.Model):
#     """User posts / activity feed entries."""
#     __tablename__ = "adm_post"

#     id        = db.Column(db.Integer, primary_key=True)
#     body      = db.Column(db.String(1000), nullable=False)
#     timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
#     user_id   = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
#     language  = db.Column(db.String(5))

#     author = db.relationship("User", backref=db.backref("posts", lazy="dynamic"))

#     def __repr__(self):
#         return f"<Post {self.body[:30]}>"


# ── Framework-level system settings ───────────────────────────────────────────

class ArasSystemSetting(ArasModel):
    """
    Framework-level key/value settings (not scoped to any app).
    Used for global toggles like script sandbox mode and dashboard builder.
    """
    __tablename__ = "aras_system_setting"
    __table_args__ = (
        db.UniqueConstraint("key", name="uq_aras_system_setting_key"),
    )

    key        = db.Column(db.String(100), nullable=False)
    label      = db.Column(db.String(200), nullable=True)
    value      = db.Column(db.Text, nullable=True)
    value_type = db.Column(db.String(20), nullable=False, default="string")
    help_text  = db.Column(db.String(500), nullable=True)
    section    = db.Column(db.String(100), nullable=True, default="general")

    def get_value(self):
        v, vt = self.value, self.value_type or "string"
        if v is None:
            return None
        try:
            if vt == "boolean": return str(v).lower() in ("1", "true", "yes", "on")
            if vt == "integer": return int(v)
            if vt == "float":   return float(v)
            if vt == "json":
                return json.loads(v)
        except (ValueError, TypeError, json.JSONDecodeError):
            pass
        return v

    def set_value(self, raw):
        vt = self.value_type or "string"
        if raw is None:
            self.value = None
            return
        if vt == "boolean":
            self.value = "true" if (raw is True or str(raw).lower() in ("1", "true", "yes", "on")) else "false"
        elif vt == "json":
            self.value = raw if isinstance(raw, str) else json.dumps(raw)
        else:
            self.value = str(raw)

    @classmethod
    def get(cls, key: str, default=None):
        row = cls.query.filter_by(key=key).first()
        return row.get_value() if row else default

    @classmethod
    def set(cls, key: str, value, value_type="string", label=None, help_text=None, section="general"):
        from arasCore.lib.extensions import db as _db
        row = cls.query.filter_by(key=key).first()
        if not row:
            row = cls(key=key, value_type=value_type,
                      label=label or key, help_text=help_text, section=section)
            _db.session.add(row)
        row.set_value(value)
        _db.session.commit()
        return row

    def __repr__(self):
        return f"<ArasSystemSetting {self.key}={self.value}>"
