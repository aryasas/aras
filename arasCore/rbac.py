# -*- coding: utf-8 -*-
"""
arasCore/rbac.py — Central authorization service.

All permission checks go through this module. Authentication (login/logout)
stays in auth.py. This separation avoids circular imports and keeps each
concern independently testable.

Dev mode: set RBAC_ENABLED=false (env) or DevelopmentConfig.RBAC_ENABLED=False
to short-circuit all checks.
"""
import logging
from functools import wraps

from flask import abort, jsonify, request, current_app
from flask_login import current_user

logger = logging.getLogger(__name__)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _rbac_enabled() -> bool:
    return current_app.config.get("RBAC_ENABLED", True)


def _parse_key(url_key: str) -> tuple[str, str | None]:
    """Split 'app/rest/of/path' → ('app', 'rest/of/path')."""
    parts = url_key.split("/", 1)
    return parts[0], parts[1] if len(parts) > 1 else None


# ── Core check ────────────────────────────────────────────────────────────────

def check_permission(user, app_slug: str, resource_slug: str | None,
                     action: str, module_slug: str | None = None) -> bool:
    """
    Return True if user may perform action on resource.

    Wildcard semantics: a Permission row with module_slug=NULL covers all
    modules; resource_slug=NULL covers all resources; action='*' covers all
    actions.

    Short-circuits when RBAC disabled or user is admin.
    """
    if not _rbac_enabled():
        return True
    if not user.is_authenticated:
        return False
    if user.is_admin:
        return True

    from arasCore.permissions import UserRole, Permission, role_permissions
    from arasCore.lib.extensions import db
    from sqlalchemy import or_

    # Collect role IDs for this user scoped to app or globally
    user_role_ids = (
        db.session.query(UserRole.role_id)
        .filter(
            UserRole.user_id == user.id,
            or_(UserRole.app_slug == None, UserRole.app_slug == app_slug),  # noqa: E711
        )
        .subquery()
    )

    # Check if any attached permission matches
    q = (
        db.session.query(Permission.id)
        .join(role_permissions, role_permissions.c.permission_id == Permission.id)
        .filter(
            role_permissions.c.role_id.in_(user_role_ids),
            Permission.app_slug == app_slug,
            or_(Permission.module_slug == None, Permission.module_slug == module_slug),  # noqa: E711
            or_(Permission.resource_slug == None, Permission.resource_slug == resource_slug),  # noqa: E711
            or_(Permission.action == "*", Permission.action == action),
        )
        .limit(1)
    )
    return q.first() is not None


# ── Allowed-resource set (for sidebar filtering) ──────────────────────────────

def get_user_allowed_resources(user, app_slug: str) -> set | None:
    """
    Return set of resource_slug strings the user has 'view' permission for,
    within app_slug. Returns None when RBAC is disabled (allow all).
    """
    if not _rbac_enabled():
        return None
    if not user.is_authenticated:
        return set()
    if user.is_admin:
        return None

    from arasCore.permissions import UserRole, Permission, role_permissions
    from arasCore.lib.extensions import db
    from sqlalchemy import or_

    user_role_ids = (
        db.session.query(UserRole.role_id)
        .filter(
            UserRole.user_id == user.id,
            or_(UserRole.app_slug == None, UserRole.app_slug == app_slug),  # noqa: E711
        )
        .subquery()
    )

    rows = (
        db.session.query(Permission.resource_slug)
        .join(role_permissions, role_permissions.c.permission_id == Permission.id)
        .filter(
            role_permissions.c.role_id.in_(user_role_ids),
            Permission.app_slug == app_slug,
            or_(Permission.action == "*", Permission.action == "view"),
        )
        .distinct()
        .all()
    )

    result = set()
    for (r,) in rows:
        if r is None:
            # Wildcard — user can view all resources in this app
            return None
        result.add(r)
    return result


# ── Decorator factory ─────────────────────────────────────────────────────────

def require_permission(app_slug: str, resource_slug: str | None, action: str,
                       module_slug: str | None = None):
    """
    Decorator factory for Flask view functions.
    Returns 403 JSON for /api/ routes, 403 HTML otherwise.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not check_permission(current_user, app_slug, resource_slug, action, module_slug):
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Forbidden"}), 403
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator


# ── Seeding ───────────────────────────────────────────────────────────────────

_ACTIONS = ("view", "create", "edit", "delete")


def seed_app_permissions(app_slug: str, resource_slugs: list[str], db,
                         module_slug: str | None = None):
    """
    Idempotent: insert view/create/edit/delete permissions for each resource.
    Called at install time, activation, and migration — safe to call repeatedly.
    """
    from arasCore.permissions import Permission

    for res_slug in resource_slugs:
        for action in _ACTIONS:
            slug = Permission.make_slug(app_slug, module_slug, res_slug, action)
            if not Permission.query.filter_by(slug=slug).first():
                perm = Permission(
                    name=Permission.make_name(app_slug, res_slug, action),
                    slug=slug,
                    app_slug=app_slug,
                    module_slug=module_slug,
                    resource_slug=res_slug,
                    action=action,
                )
                db.session.add(perm)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.warning(f"[rbac] seed_app_permissions failed for {app_slug}: {e}")


def seed_app_permissions_from_helper(helper, db):
    """
    Walk an AppHelper and seed permissions for all resources, preserving
    module_slug from MenuGroup context.
    """
    from arasCore.permissions import Permission

    pairs = []  # [(module_slug, resource_slug), ...]

    for res in getattr(helper, "resources", []):
        pairs.append((None, res.name))

    for group in getattr(helper, "menu_groups", []):
        mod_slug = group.title.lower().replace(" ", "_")
        for res in getattr(group, "resources", []):
            pairs.append((mod_slug, res.name))

    for module_slug, res_slug in pairs:
        for action in _ACTIONS:
            slug = Permission.make_slug(helper.name, module_slug, res_slug, action)
            if not Permission.query.filter_by(slug=slug).first():
                perm = Permission(
                    name=Permission.make_name(helper.name, res_slug, action),
                    slug=slug,
                    app_slug=helper.name,
                    module_slug=module_slug,
                    resource_slug=res_slug,
                    action=action,
                )
                db.session.add(perm)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.warning(f"[rbac] seed_app_permissions_from_helper failed for {helper.name}: {e}")


def unseed_app_permissions(app_slug: str, db):
    """Remove all permissions for an app. Called when app is deleted."""
    from arasCore.permissions import Permission

    try:
        Permission.query.filter_by(app_slug=app_slug).delete()
        db.session.commit()
        logger.info(f"[rbac] permissions removed for app '{app_slug}'")
    except Exception as e:
        db.session.rollback()
        logger.warning(f"[rbac] unseed_app_permissions failed for {app_slug}: {e}")
