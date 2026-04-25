# -*- coding: utf-8 -*-
"""arasCore/permissions.py — Role, Permission, UserRole models."""
from .lib.extensions import db
from .lib.base_model import ArasModel

role_permissions = db.Table(
    "auth_role_permissions",
    db.Column("role_id",       db.Integer, db.ForeignKey("auth_roles.id"),       primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("auth_permissions.id"), primary_key=True),
)


class Role(ArasModel):
    __tablename__ = "auth_roles"

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(64),  unique=True, nullable=False)
    slug        = db.Column(db.String(64),  unique=True, nullable=False)
    description = db.Column(db.String(256), nullable=True)
    is_active   = db.Column(db.Boolean, default=True)
    permissions = db.relationship("Permission", secondary=role_permissions, backref="roles")

    def __repr__(self):
        return f"<Role {self.slug}>"


class Permission(ArasModel):
    """
    Hierarchical permission: app → module → resource → action.
    NULL in module_slug/resource_slug acts as wildcard (covers all children).
    """
    __tablename__ = "auth_permissions"
    __table_args__ = (
        db.UniqueConstraint("app_slug", "module_slug", "resource_slug", "action",
                            name="uq_perm_scope"),
        db.Index("ix_perm_app", "app_slug"),
        db.Index("ix_perm_app_mod", "app_slug", "module_slug"),
        db.Index("ix_perm_app_mod_res", "app_slug", "module_slug", "resource_slug"),
    )

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(128), nullable=False)
    # canonical: "{app_slug}:{module_slug or '*'}:{resource_slug or '*'}:{action}"
    slug          = db.Column(db.String(256), unique=True, nullable=False)
    app_slug      = db.Column(db.String(64),  nullable=False)
    module_slug   = db.Column(db.String(64),  nullable=True)   # NULL = all modules
    resource_slug = db.Column(db.String(128), nullable=True)   # NULL = all resources
    action        = db.Column(db.String(16),  nullable=False)  # view|create|edit|delete|*

    @classmethod
    def make_slug(cls, app_slug, module_slug, resource_slug, action):
        m = module_slug or "*"
        r = resource_slug or "*"
        return f"{app_slug}:{m}:{r}:{action}"

    @classmethod
    def make_name(cls, app_slug, resource_slug, action):
        r = resource_slug or app_slug
        return f"{action.capitalize()} {r.replace('/', ' ').replace('_', ' ').title()}"

    def __repr__(self):
        return f"<Permission {self.slug}>"


class UserRole(ArasModel):
    __tablename__ = "auth_user_roles"
    __table_args__ = (
        db.UniqueConstraint("user_id", "role_id", "app_slug", name="uq_user_role_app"),
        db.Index("ix_userrole_user", "user_id"),
    )

    id       = db.Column(db.Integer, primary_key=True)
    user_id  = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    role_id  = db.Column(db.Integer, db.ForeignKey("auth_roles.id"), nullable=False)
    # NULL = global role; set to app slug to scope role to one app
    app_slug = db.Column(db.String(64), nullable=True)
    user     = db.relationship("User", foreign_keys=[user_id], back_populates="roles")
    role     = db.relationship("Role")
