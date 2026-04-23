# -*- coding: utf-8 -*-
"""
arasCore/lib/migrations/m002_rbac.py
=====================================
Idempotent migration to upgrade RBAC tables to the hierarchical schema and
seed base permissions for all registered apps.

Changes:
  auth_roles        — add description, is_active; drop scope
  auth_permissions  — recreate with app_slug/module_slug/resource_slug/action
  auth_role_permissions — recreate if stale FK references exist
  auth_user_roles   — add app_slug (VARCHAR); retire app_id (kept, dropped in m003)
  mgr_table         — add required_role_slug

Safe to re-run: every ALTER checks information_schema first.
"""
import logging

logger = logging.getLogger(__name__)


def _col_exists(conn, table, column):
    from sqlalchemy import text
    return conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() "
        f"AND TABLE_NAME = '{table}' AND COLUMN_NAME = '{column}'"
    )).scalar()


def _table_exists(conn, table):
    from sqlalchemy import text
    return conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA = DATABASE() "
        f"AND TABLE_NAME = '{table}'"
    )).scalar()


def _index_exists(conn, table, index_name):
    from sqlalchemy import text
    return conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.STATISTICS "
        "WHERE TABLE_SCHEMA = DATABASE() "
        f"AND TABLE_NAME = '{table}' AND INDEX_NAME = '{index_name}'"
    )).scalar()


def run(flask_app):
    """Apply migration. Idempotent."""
    from arasCore.lib.extensions import db
    from sqlalchemy import text

    with flask_app.app_context():
        engine = db.engine
        with engine.begin() as conn:

            # ── 1. auth_roles — add description, is_active; drop scope ────────
            if not _col_exists(conn, "auth_roles", "description"):
                conn.execute(text("ALTER TABLE auth_roles ADD COLUMN description VARCHAR(256) NULL"))
                logger.info("[m002] auth_roles.description added")

            if not _col_exists(conn, "auth_roles", "is_active"):
                conn.execute(text("ALTER TABLE auth_roles ADD COLUMN is_active TINYINT(1) DEFAULT 1"))
                logger.info("[m002] auth_roles.is_active added")

            if _col_exists(conn, "auth_roles", "scope"):
                conn.execute(text("ALTER TABLE auth_roles DROP COLUMN scope"))
                logger.info("[m002] auth_roles.scope dropped")

            # ── 2. auth_permissions — recreate with new columns ───────────────
            # Detect old schema by checking for 'resource' column (old) vs 'app_slug' (new)
            old_schema = _col_exists(conn, "auth_permissions", "resource")
            new_schema = _col_exists(conn, "auth_permissions", "app_slug")

            if old_schema and not new_schema:
                # Drop FK join table first to avoid FK constraint error
                conn.execute(text("DROP TABLE IF EXISTS auth_role_permissions"))
                conn.execute(text("DROP TABLE IF EXISTS auth_permissions"))
                logger.info("[m002] auth_permissions (old schema) dropped")

            if not _table_exists(conn, "auth_permissions"):
                conn.execute(text("""
                    CREATE TABLE auth_permissions (
                        id            INT AUTO_INCREMENT PRIMARY KEY,
                        name          VARCHAR(128) NOT NULL,
                        slug          VARCHAR(256) NOT NULL UNIQUE,
                        app_slug      VARCHAR(64)  NOT NULL,
                        module_slug   VARCHAR(64)  NULL,
                        resource_slug VARCHAR(128) NULL,
                        action        VARCHAR(16)  NOT NULL,
                        UNIQUE KEY uq_perm_scope (app_slug, module_slug, resource_slug, action),
                        INDEX ix_perm_app (app_slug),
                        INDEX ix_perm_app_mod (app_slug, module_slug),
                        INDEX ix_perm_app_mod_res (app_slug, module_slug, resource_slug)
                    ) CHARACTER SET utf8mb4
                """))
                logger.info("[m002] auth_permissions (new schema) created")

            # ── 3. auth_role_permissions — recreate if missing ────────────────
            if not _table_exists(conn, "auth_role_permissions"):
                conn.execute(text("""
                    CREATE TABLE auth_role_permissions (
                        role_id       INT NOT NULL,
                        permission_id INT NOT NULL,
                        PRIMARY KEY (role_id, permission_id),
                        FOREIGN KEY (role_id)       REFERENCES auth_roles(id)       ON DELETE CASCADE,
                        FOREIGN KEY (permission_id) REFERENCES auth_permissions(id) ON DELETE CASCADE
                    ) CHARACTER SET utf8mb4
                """))
                logger.info("[m002] auth_role_permissions created")

            # ── 4. auth_user_roles — add app_slug, unique constraint ──────────
            if not _col_exists(conn, "auth_user_roles", "app_slug"):
                conn.execute(text("ALTER TABLE auth_user_roles ADD COLUMN app_slug VARCHAR(64) NULL"))
                logger.info("[m002] auth_user_roles.app_slug added")

            if not _index_exists(conn, "auth_user_roles", "uq_user_role_app"):
                try:
                    conn.execute(text(
                        "ALTER TABLE auth_user_roles "
                        "ADD UNIQUE KEY uq_user_role_app (user_id, role_id, app_slug)"
                    ))
                    logger.info("[m002] auth_user_roles unique constraint added")
                except Exception as e:
                    logger.warning(f"[m002] could not add unique constraint (duplicate data?): {e}")

            if not _index_exists(conn, "auth_user_roles", "ix_userrole_user"):
                conn.execute(text(
                    "ALTER TABLE auth_user_roles ADD INDEX ix_userrole_user (user_id)"
                ))
                logger.info("[m002] auth_user_roles.ix_userrole_user added")

            # ── 5. mgr_table — add required_role_slug ────────────────────────
            if _table_exists(conn, "mgr_table") and not _col_exists(conn, "mgr_table", "required_role_slug"):
                conn.execute(text("ALTER TABLE mgr_table ADD COLUMN required_role_slug VARCHAR(64) NULL"))
                logger.info("[m002] mgr_table.required_role_slug added")

        # ── 6. Seed permissions (outside transaction — uses SQLAlchemy ORM) ──
        _seed_permissions(flask_app)

        logger.info("[m002] migration complete.")


def _seed_permissions(flask_app):
    """Seed view/create/edit/delete permissions for all registered apps."""
    from arasCore.rbac import seed_app_permissions, seed_app_permissions_from_helper
    from arasCore.lib.extensions import db

    with flask_app.app_context():
        # Code-based apps (already registered via _register_helper at startup)
        try:
            from arasCore.lib.blueprints import get_helper_registry
            for helper in get_helper_registry().values():
                seed_app_permissions_from_helper(helper, db)
                logger.info(f"[m002] seeded permissions for code-based app: {helper.name}")
        except Exception as e:
            logger.warning(f"[m002] code-based seed failed: {e}")

        # Dynamic apps from DB
        try:
            from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable
            apps = AppManagerApp.query.all()
            for app in apps:
                tables = AppManagerTable.query.filter_by(app_id=app.id, is_active=True).all()
                resource_slugs = [t.name for t in tables]
                if resource_slugs:
                    seed_app_permissions(app.slug, resource_slugs, db)
                    logger.info(f"[m002] seeded permissions for dynamic app: {app.slug}")
        except Exception as e:
            logger.warning(f"[m002] dynamic app seed failed: {e}")
