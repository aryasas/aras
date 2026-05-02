# -*- coding: utf-8 -*-
"""
arasCore/lib/schema_migrator.py
================================
Schema migration runner for dynamic apps.

Problem: AppManagerColumn records are the source of truth for a dynamic app's
schema, but db.create_all() only creates *missing* tables — it never alters
existing ones. When an admin adds a column to an existing table, the physical DB
column must be added via ALTER TABLE.

This module:
  - Diffs AppManagerColumn snapshot against the live table (via SA inspector)
  - Records needed ALTER TABLE stubs into mgr_schema_migration
  - Auto-applies safe ops (add nullable column)
  - Leaves unsafe ops (type change, rename, drop) in 'pending' status for manual review

Public API:
  diff_app(app_id, flask_app)   → list of MigrationRecord
  apply_pending(app_id, flask_app, safe_only=True) → (applied, skipped)
  get_pending(app_id) → list of dicts
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Field type → SQL type (mirrors _make_sa_column in services.py)
_FIELD_TO_SQL = {
    "string":   "VARCHAR(200)",
    "email":    "VARCHAR(200)",
    "url":      "VARCHAR(500)",
    "text":     "TEXT",
    "integer":  "INT",
    "float":    "FLOAT",
    "decimal":  "DECIMAL(15,4)",
    "boolean":  "TINYINT(1) DEFAULT 0",
    "date":     "DATE",
    "datetime": "DATETIME",
    "json":     "JSON",
    "relation": "INT",
    "select":   "VARCHAR(100)",
    "currency": "DECIMAL(15,4)",
}

_SAFE_ACTIONS = {"add_column"}


def _col_sql(col_def: dict) -> str:
    """Build SQL type fragment for a column definition dict."""
    ft = col_def.get("field_type", "string")
    sql_type = _FIELD_TO_SQL.get(ft, "VARCHAR(200)")
    nullable = " NULL" if not col_def.get("required") else " NOT NULL"
    default = ""
    if col_def.get("default_value") not in (None, ""):
        v = col_def["default_value"]
        if ft in ("boolean", "integer", "float", "decimal", "currency"):
            default = f" DEFAULT {v}"
        else:
            v_escaped = str(v).replace("'", "''")
            default = f" DEFAULT '{v_escaped}'"
    return f"{sql_type}{nullable}{default}"


def diff_app(app_id: int, flask_app=None):
    """
    Compare AppManagerColumn records against the live DB table for every
    table in app_id. Returns list of new MigrationRecord ORM objects (not yet
    committed).

    Already-recorded migrations are skipped (idempotent).
    """
    from arasCore.lib.core.extensions import db
    from arasCore.admin.models import AppManagerApp, AppManagerTable, AppManagerColumn
    from sqlalchemy import inspect as sa_inspect

    app_obj = AppManagerApp.query.get(app_id)
    if not app_obj:
        return []

    inspector = sa_inspect(db.engine)
    records = []

    # Get all active tables for this app
    app_tables = AppManagerTable.query.filter_by(app_id=app_id, is_active=True).all()
    
    for tbl in app_tables:
        tbl_name = tbl.db_table_name or f"ab_{app_obj.slug}_{tbl.name}"

        # Get live columns
        try:
            live_cols_raw = inspector.get_columns(tbl_name)
            live_cols = {c["name"]: c for c in live_cols_raw}
        except Exception:
            # Table might not exist yet (db.create_all hasn't run or failed)
            continue

        # 1. Check for NEW columns or TYPE CHANGES
        mgr_cols = AppManagerColumn.query.filter_by(table_id=tbl.id).order_by(AppManagerColumn.order).all()
        mgr_col_names = set()
        
        for col in mgr_cols:
            mgr_col_names.add(col.name)
            col_sql_type = _col_sql(col.__dict__)
            
            if col.name not in live_cols:
                # NEW COLUMN
                existing = _get_migration_record(app_obj.slug, tbl_name, col.name, "add_column")
                if not existing:
                    sql_stmt = f"ALTER TABLE `{tbl_name}` ADD COLUMN `{col.name}` {col_sql_type}"
                    rec = _create_migration_record(
                        app_name=app_obj.slug,
                        table_name=tbl_name,
                        column_name=col.name,
                        action="add_column",
                        sql_stmt=sql_stmt,
                        db=db,
                    )
                    records.append(rec)
            else:
                # Check for type change (simplified)
                # This is a bit naive but catches obvious changes
                live_type = str(live_cols[col.name]["type"]).upper()
                target_type = col_sql_type.split(" ")[0].upper()
                
                # Basic normalization for comparison
                if "VARCHAR" in live_type and "VARCHAR" in target_type:
                    # Ignore length diff for now or implement deeper check
                    pass
                elif "INT" in live_type and "INT" in target_type:
                    pass
                elif live_type != target_type and not (live_type.startswith(target_type) or target_type.startswith(live_type)):
                    # Possible type change
                    existing = _get_migration_record(app_obj.slug, tbl_name, col.name, "change_type")
                    if not existing:
                        # Unsafe operation: use CHANGE or MODIFY
                        sql_stmt = f"ALTER TABLE `{tbl_name}` MODIFY COLUMN `{col.name}` {col_sql_type}"
                        rec = _create_migration_record(
                            app_name=app_obj.slug,
                            table_name=tbl_name,
                            column_name=col.name,
                            action="change_type",
                            sql_stmt=sql_stmt,
                            db=db,
                        )
                        records.append(rec)

        # 2. Check for DROPPED columns (In DB but not in Manager)
        for live_col_name in live_cols:
            # Skip system columns usually
            if live_col_name in ("id", "created_at", "updated_at", "owner_id", "is_deleted", "deleted_at"):
                continue
                
            if live_col_name not in mgr_col_names:
                existing = _get_migration_record(app_obj.slug, tbl_name, live_col_name, "drop_column")
                if not existing:
                    sql_stmt = f"ALTER TABLE `{tbl_name}` DROP COLUMN `{live_col_name}`"
                    rec = _create_migration_record(
                        app_name=app_obj.slug,
                        table_name=tbl_name,
                        column_name=live_col_name,
                        action="drop_column",
                        sql_stmt=sql_stmt,
                        db=db,
                    )
                    records.append(rec)

    if records:
        db.session.commit()

    return records


def apply_pending(app_id: int, flask_app=None, safe_only: bool = True):
    """
    Apply pending migrations for app_id.

    safe_only=True (default): only applies add_column (safe); leaves type
    changes and renames as pending for manual review.

    Returns (applied: list[dict], skipped: list[dict]).
    """
    from arasCore.lib.core.extensions import db
    from arasCore.admin.models import AppManagerApp
    from sqlalchemy import text

    app_obj = AppManagerApp.query.get(app_id)
    if not app_obj:
        return [], []

    pending = _list_pending(app_obj.slug, db)
    applied, skipped = [], []

    for row in pending:
        # action is 'add_column', 'drop_column', or 'change_type'
        if safe_only and row["action"] not in _SAFE_ACTIONS:
            skipped.append(row)
            continue

        try:
            with db.engine.connect() as conn:
                conn.execute(text(row["sql_stmt"]))
                conn.commit()
            _mark_applied(row["id"], db)
            applied.append(row)
            logger.info(f"[schema_migrator] applied: {row['sql_stmt']}")
        except Exception as e:
            _mark_error(row["id"], str(e), db)
            skipped.append({**row, "error": str(e)})
            logger.warning(f"[schema_migrator] failed: {row['sql_stmt']} — {e}")

    return applied, skipped


def get_pending(app_id: int):
    """Return list of pending migration dicts for app_id."""
    from arasCore.lib.core.extensions import db
    from arasCore.admin.models import AppManagerApp

    app_obj = AppManagerApp.query.get(app_id)
    if not app_obj:
        return []
    return _list_pending(app_obj.slug, db)


def get_history(app_id: int, limit: int = 50):
    """Return list of recently applied or failed migration dicts for app_id."""
    from arasCore.lib.core.extensions import db
    from arasCore.admin.models import AppManagerApp
    from sqlalchemy import text

    app_obj = AppManagerApp.query.get(app_id)
    if not app_obj:
        return []
        
    try:
        rows = db.session.execute(text(
            "SELECT id, app_name, table_name, column_name, action, status, sql_stmt, error_msg, applied_at, created_at "
            "FROM mgr_schema_migration WHERE app_name=:a AND status != 'pending' "
            "ORDER BY COALESCE(applied_at, created_at) DESC LIMIT :limit"
        ), {"a": app_obj.slug, "limit": limit}).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception as e:
        logger.error(f"get_history error: {e}")
        return []


# ── Internal helpers ──────────────────────────────────────────────────────────

def _get_migration_record(app_name, table_name, column_name, action=None):
    from arasCore.lib.core.extensions import db
    from sqlalchemy import text
    try:
        query = "SELECT id FROM mgr_schema_migration WHERE app_name=:a AND table_name=:t AND column_name=:c"
        params = {"a": app_name, "t": table_name, "c": column_name}
        if action:
            query += " AND action=:act"
            params["act"] = action
            
        row = db.session.execute(text(query), params).fetchone()
        return row
    except Exception:
        return None


def _create_migration_record(app_name, table_name, column_name, action, sql_stmt, db):
    from sqlalchemy import text
    db.session.execute(text(
        "INSERT INTO mgr_schema_migration "
        "(app_name, table_name, column_name, action, status, sql_stmt) "
        "VALUES (:a, :t, :c, :act, 'pending', :sql)"
    ), {"a": app_name, "t": table_name, "c": column_name, "act": action, "sql": sql_stmt})
    return {"app_name": app_name, "table_name": table_name, "column_name": column_name,
            "action": action, "sql_stmt": sql_stmt}


def _list_pending(app_name, db):
    from sqlalchemy import text
    try:
        rows = db.session.execute(text(
            "SELECT id, app_name, table_name, column_name, action, sql_stmt "
            "FROM mgr_schema_migration WHERE app_name=:a AND status='pending'"
        ), {"a": app_name}).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception:
        return []


def _mark_applied(migration_id, db):
    from sqlalchemy import text
    db.session.execute(text(
        "UPDATE mgr_schema_migration SET status='applied', applied_at=:ts WHERE id=:id"
    ), {"ts": datetime.utcnow(), "id": migration_id})
    db.session.commit()


def _mark_error(migration_id, error_msg, db):
    from sqlalchemy import text
    db.session.execute(text(
        "UPDATE mgr_schema_migration SET status='error', error_msg=:e WHERE id=:id"
    ), {"e": error_msg[:1000], "id": migration_id})
    db.session.commit()
