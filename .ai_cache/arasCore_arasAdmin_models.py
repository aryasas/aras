# -*- coding: utf-8 -*-
"""
arasCore/arasAdmin/models.py
Admin + Builder models.
Migrated from app_manager/models.py and app_admin/models.py.
"""
from datetime import datetime
from time import time
import json
from arasCore.lib.extensions import db


# ── App Manager ───────────────────────────────────────────────────────────────

class AppManagerApp(db.Model):
    """
    Defines a dynamically-built application.
    Replaces physical app_* folders — everything stored in DB.
    """
    __tablename__ = "mgr_app"

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), unique=True, nullable=False)   # internal slug
    title      = db.Column(db.String(200), nullable=False)                # display title
    main_title = db.Column(db.String(200), nullable=False)                # nav/sidebar title
    url        = db.Column(db.String(200), nullable=False)                # URL prefix e.g. /notes
    endpoint   = db.Column(db.String(100), nullable=False)                # blueprint endpoint
    is_active  = db.Column(db.Boolean, default=True, nullable=False)
    in_sidebar = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    def get_tables(self):
        return self.tables.order_by(AppManagerTable.menu_order).all()

    def get_fields(self):
        return self.fields.order_by(AppManagerField.order).all()

    def to_dict(self):
        return {
            "id":         self.id,
            "name":       self.name,
            "title":      self.title,
            "main_title": self.main_title,
            "url":        self.url,
            "endpoint":   self.endpoint,
            "is_active":  self.is_active,
            "in_sidebar": self.in_sidebar,
            "fields":     [f.to_dict() for f in self.get_fields()],
        }

    def __repr__(self):
        return f"<AppManagerApp {self.name}>"


class AppManagerTable(db.Model):
    """
    One table/page within an AppManagerApp.
    Each table generates: 1 DB table + 1 set of CRUD pages + 1 menu entry.
    """
    __tablename__ = "mgr_table"

    id              = db.Column(db.Integer, primary_key=True)
    app_id          = db.Column(db.Integer, db.ForeignKey("mgr_app.id"), nullable=False)
    parent_table_id = db.Column(db.Integer, db.ForeignKey("mgr_table.id"), nullable=True)

    name            = db.Column(db.String(100), nullable=False)   # slug, e.g. "products"
    title           = db.Column(db.String(200), nullable=False)   # display, e.g. "Products"
    url_suffix      = db.Column(db.String(200), nullable=False, default="")  # e.g. "/products"
    db_table_name   = db.Column(db.String(200), nullable=True)    # override; default ab_{app}_{name}

    # Menu settings
    menu_title      = db.Column(db.String(200), nullable=True)    # defaults to title
    menu_icon       = db.Column(db.String(50),  default="fa-table")
    show_in_menu    = db.Column(db.Boolean, default=True)
    menu_order      = db.Column(db.Integer, default=0)

    is_active       = db.Column(db.Boolean, default=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    # Table-level settings
    search_enabled  = db.Column(db.Boolean, default=True)
    sort_field      = db.Column(db.String(100), nullable=True)
    sort_direction  = db.Column(db.String(4), default="asc")
    list_columns    = db.Column(db.Text, nullable=True)   # comma-separated column names
    allow_create    = db.Column(db.Boolean, default=True)
    allow_edit      = db.Column(db.Boolean, default=True)
    allow_delete    = db.Column(db.Boolean, default=True)
    detail_view     = db.Column(db.Boolean, default=False)

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

    def get_columns(self):
        return self.columns.order_by(AppManagerColumn.order).all()

    def get_db_table_name(self, app_name):
        return self.db_table_name or f"ab_{app_name}_{self.name}"

    def get_full_url(self, app_url):
        return f"{app_url}{self.url_suffix}"

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


class AppManagerColumn(db.Model):
    """A column/field within an AppManagerTable."""
    __tablename__ = "mgr_column"

    FIELD_TYPES = [
        "string", "text", "integer", "float", "decimal", "boolean",
        "date", "datetime", "email", "url", "phone", "select",
        "file", "image", "json", "uuid", "relation",
    ]

    id         = db.Column(db.Integer, primary_key=True)
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

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
            "relation_table_id":     self.relation_table_id,
            "relation_system_table": self.relation_system_table,
            "relation_display_col":  self.relation_display_col,
            "cascade_delete":        self.cascade_delete,
        }

    def __repr__(self):
        return f"<AppManagerColumn {self.name}:{self.field_type}>"


# Keep for backward compat — routes/services may still reference this
class AppManagerField(db.Model):
    """Deprecated — use AppManagerColumn via AppManagerTable instead."""
    __tablename__ = "mgr_field"

    id         = db.Column(db.Integer, primary_key=True)
    app_id     = db.Column(db.Integer, db.ForeignKey("mgr_app.id"), nullable=False)
    name       = db.Column(db.String(100), nullable=False)
    label      = db.Column(db.String(200), nullable=False)
    field_type = db.Column(db.String(50),  nullable=False, default="string")
    required   = db.Column(db.Boolean, default=False)
    order      = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "app_id": self.app_id, "name": self.name,
            "label": self.label, "field_type": self.field_type,
            "required": self.required, "order": self.order,
        }

    def __repr__(self):
        return f"<AppManagerField {self.name}:{self.field_type}>"


# ── Menu Definition (DB-driven nav) ──────────────────────────────────────────

class MenuDefinition(db.Model):
    """Top navbar menu entries, generated from active apps + roles."""
    __tablename__ = "mgr_menu"

    id         = db.Column(db.Integer, primary_key=True)
    app_id     = db.Column(db.Integer, db.ForeignKey("mgr_app.id"), nullable=True)
    title      = db.Column(db.String(100), nullable=False)
    url        = db.Column(db.String(200))
    icon       = db.Column(db.String(50))
    order      = db.Column(db.Integer, default=0)
    role_slug  = db.Column(db.String(64), nullable=True)   # null = visible to all
    is_active  = db.Column(db.Boolean, default=True)

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

class Notification(db.Model):
    """User notifications (badge counts, alerts)."""
    __tablename__ = "adm_notification"

    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(128), index=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    timestamp    = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)
    category     = db.Column(db.String(128))

    user = db.relationship("User", backref=db.backref("notifications", lazy="dynamic"))

    def get_data(self):
        return json.loads(str(self.payload_json))

    def __repr__(self):
        return f"<Notification {self.name}>"


# ── User Activity ─────────────────────────────────────────────────────────────

class UserActivity(db.Model):
    """Audit log of user actions."""
    __tablename__ = "adm_user_activity"

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    name         = db.Column(db.String(128), index=True)
    module       = db.Column(db.String(128))
    payload_json = db.Column(db.Text)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("activities", lazy="dynamic"))

    def get_data(self):
        return json.loads(str(self.payload_json)) if self.payload_json else {}

    def __repr__(self):
        return f"<UserActivity {self.name}>"


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
