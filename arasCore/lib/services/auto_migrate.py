# -*- coding: utf-8 -*-
"""
arasCore/lib/services/auto_migrate.py
=====================================
Boot-time DB reconciler. Reads SQLAlchemy metadata (every model declared
via ArasModel or db.Model) and the live DB schema, computes a diff, and
applies safe changes in-place — no migration files, no flask db migrate.

Policy
------
SAFE  (always applied):
    - create new table
    - add new column (nullable, or with default/server_default)
    - add new index
    - add new FK
    - widen VARCHAR length

DESTRUCTIVE  (only when ARAS_AUTO_DROP=true):
    - drop column
    - drop table
    - drop index
    - narrow type
    - add NOT NULL on existing column

ABORT  (refuse to proceed):
    - autoload errors (don't drop tables when model set is incomplete)

Source of truth = the live SQLAlchemy metadata after all models import.
mgr_column rows are kept in sync (cleaned up when columns drop).
"""
from __future__ import annotations
import os
import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy import String, Numeric, Text

logger = logging.getLogger(__name__)


# ── Config ──────────────────────────────────────────────────────────────────

def _allow_drop() -> bool:
    return os.environ.get("ARAS_AUTO_DROP", "").lower() in ("1", "true", "yes", "on")


def _enabled() -> bool:
    val = os.environ.get("ARAS_AUTO_MIGRATE", "true").lower()
    return val in ("1", "true", "yes", "on")


# ── Diff result ─────────────────────────────────────────────────────────────

@dataclass
class MigrationReport:
    created_tables:  list[str] = field(default_factory=list)
    added_columns:   list[str] = field(default_factory=list)
    added_indexes:   list[str] = field(default_factory=list)
    widened_columns: list[str] = field(default_factory=list)
    dropped_tables:  list[str] = field(default_factory=list)
    dropped_columns: list[str] = field(default_factory=list)
    skipped_unsafe:  list[str] = field(default_factory=list)
    errors:          list[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return any([
            self.created_tables, self.added_columns, self.added_indexes,
            self.widened_columns, self.dropped_tables, self.dropped_columns,
        ])

    def log_summary(self):
        if not self.has_changes() and not self.skipped_unsafe and not self.errors:
            logger.info("[auto_migrate] schema in sync — no changes")
            return
        if self.created_tables:
            logger.info(f"[auto_migrate] created tables: {self.created_tables}")
        if self.added_columns:
            logger.info(f"[auto_migrate] added columns: {self.added_columns}")
        if self.added_indexes:
            logger.info(f"[auto_migrate] added indexes: {self.added_indexes}")
        if self.widened_columns:
            logger.info(f"[auto_migrate] widened: {self.widened_columns}")
        if self.dropped_tables:
            logger.warning(f"[auto_migrate] DROPPED tables: {self.dropped_tables}")
        if self.dropped_columns:
            logger.warning(f"[auto_migrate] DROPPED columns: {self.dropped_columns}")
        if self.skipped_unsafe:
            logger.warning(f"[auto_migrate] SKIPPED (set ARAS_AUTO_DROP=true to apply): {self.skipped_unsafe}")
        if self.errors:
            logger.error(f"[auto_migrate] errors: {self.errors}")


# ── Helpers ─────────────────────────────────────────────────────────────────

def _column_type_sql(col, dialect) -> str:
    return col.type.compile(dialect=dialect)


def _safe_default_sql(col) -> str | None:
    """Return inline DEFAULT clause for ADD COLUMN, or None."""
    if col.server_default is not None:
        sd = col.server_default
        try:
            return sd.arg.text if hasattr(sd, "arg") and hasattr(sd.arg, "text") else None
        except Exception:
            return None
    if col.default is not None and getattr(col.default, "is_scalar", False):
        v = col.default.arg
        if isinstance(v, bool):
            return "1" if v else "0"
        if isinstance(v, (int, float)):
            return str(v)
        if isinstance(v, str):
            return f"'{v}'"
    return None


def _quote(name: str) -> str:
    return f"`{name}`"


# ── The engine ──────────────────────────────────────────────────────────────

def run(flask_app, *, autoload_had_errors: bool = False) -> MigrationReport:
    report = MigrationReport()

    if not _enabled():
        logger.info("[auto_migrate] disabled (ARAS_AUTO_MIGRATE=false)")
        return report

    if autoload_had_errors:
        logger.error("[auto_migrate] aborting: autoload had import errors — refusing to risk drops")
        report.errors.append("autoload had errors")
        return report

    from arasCore.lib.core.extensions import db

    with flask_app.app_context():
        try:
            insp   = sa_inspect(db.engine)
            meta   = db.metadata
            engine = db.engine
            dialect = engine.dialect
            db_tables = set(insp.get_table_names())
            model_tables = set(meta.tables.keys())

            allow_drop = _allow_drop()

            # ── 1. Create new tables ──
            for tname in sorted(model_tables - db_tables):
                tbl = meta.tables[tname]
                try:
                    tbl.create(bind=engine)
                    report.created_tables.append(tname)
                except Exception as e:
                    report.errors.append(f"create {tname}: {e}")

            # ── 2. Diff existing tables ──
            for tname in sorted(model_tables & db_tables):
                tbl = meta.tables[tname]
                live_cols = {c["name"]: c for c in insp.get_columns(tname)}
                model_cols = {c.name: c for c in tbl.columns}

                # add missing columns
                for cname in sorted(set(model_cols) - set(live_cols)):
                    col = model_cols[cname]
                    try:
                        type_sql = _column_type_sql(col, dialect)
                        nullable_sql = "" if col.nullable else " NOT NULL"
                        default = _safe_default_sql(col)
                        default_sql = f" DEFAULT {default}" if default is not None else ""
                        if not col.nullable and default is None:
                            report.skipped_unsafe.append(f"{tname}.{cname}: NOT NULL without default")
                            continue
                        sql = f"ALTER TABLE {_quote(tname)} ADD COLUMN {_quote(cname)} {type_sql}{default_sql}{nullable_sql}"
                        with engine.begin() as conn:
                            from sqlalchemy import text
                            conn.execute(text(sql))
                        report.added_columns.append(f"{tname}.{cname}")
                    except Exception as e:
                        report.errors.append(f"add {tname}.{cname}: {e}")

                # widen VARCHAR
                for cname in sorted(set(model_cols) & set(live_cols)):
                    mcol = model_cols[cname]
                    lcol = live_cols[cname]
                    if isinstance(mcol.type, String) and not isinstance(mcol.type, Text):
                        m_len = getattr(mcol.type, "length", None) or 0
                        l_type = lcol.get("type")
                        l_len  = getattr(l_type, "length", None) or 0
                        if m_len and l_len and m_len > l_len:
                            try:
                                type_sql = _column_type_sql(mcol, dialect)
                                nullable_sql = "" if mcol.nullable else " NOT NULL"
                                sql = f"ALTER TABLE {_quote(tname)} MODIFY {_quote(cname)} {type_sql}{nullable_sql}"
                                from sqlalchemy import text
                                with engine.begin() as conn:
                                    conn.execute(text(sql))
                                report.widened_columns.append(f"{tname}.{cname} ({l_len}→{m_len})")
                            except Exception as e:
                                report.errors.append(f"widen {tname}.{cname}: {e}")
                        elif m_len and l_len and m_len < l_len:
                            report.skipped_unsafe.append(f"{tname}.{cname}: narrow VARCHAR {l_len}→{m_len}")

                # drop columns (gated)
                drop_cols = set(live_cols) - set(model_cols)
                for cname in sorted(drop_cols):
                    label = f"{tname}.{cname}"
                    if not allow_drop:
                        report.skipped_unsafe.append(f"DROP COLUMN {label}")
                        continue
                    try:
                        from sqlalchemy import text
                        with engine.begin() as conn:
                            conn.execute(text(f"ALTER TABLE {_quote(tname)} DROP COLUMN {_quote(cname)}"))
                        report.dropped_columns.append(label)
                    except Exception as e:
                        report.errors.append(f"drop {label}: {e}")

                # add missing indexes
                try:
                    live_idx = {i["name"] for i in insp.get_indexes(tname)}
                    for idx in tbl.indexes:
                        if idx.name and idx.name not in live_idx:
                            try:
                                idx.create(bind=engine)
                                report.added_indexes.append(f"{tname}.{idx.name}")
                            except Exception as e:
                                report.errors.append(f"index {tname}.{idx.name}: {e}")
                except Exception:
                    pass

            # ── 3. Drop tables not in any model (gated) ──
            for tname in sorted(db_tables - model_tables):
                # Skip framework-managed tables that may exist without an ArasModel
                if tname.startswith("alembic_"):
                    continue
                if not allow_drop:
                    report.skipped_unsafe.append(f"DROP TABLE {tname}")
                    continue
                try:
                    from sqlalchemy import text
                    with engine.begin() as conn:
                        conn.execute(text(f"DROP TABLE {_quote(tname)}"))
                    report.dropped_tables.append(tname)
                except Exception as e:
                    report.errors.append(f"drop table {tname}: {e}")

            # ── 4. Clean up mgr_column rows for dropped columns ──
            if report.dropped_columns or report.dropped_tables:
                try:
                    from arasCore.admin.models import AppManagerColumn, AppManagerTable
                    for ent in report.dropped_columns:
                        tname, cname = ent.split(".", 1)
                        tbl_row = AppManagerTable.query.filter(
                            (AppManagerTable.name == tname) | (AppManagerTable.db_table_name == tname)
                        ).first()
                        if tbl_row:
                            AppManagerColumn.query.filter_by(table_id=tbl_row.id, name=cname).delete()
                    for tname in report.dropped_tables:
                        tbl_row = AppManagerTable.query.filter(
                            (AppManagerTable.name == tname) | (AppManagerTable.db_table_name == tname)
                        ).first()
                        if tbl_row:
                            AppManagerColumn.query.filter_by(table_id=tbl_row.id).delete()
                            db.session.delete(tbl_row)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    logger.warning(f"[auto_migrate] mgr_column cleanup failed: {e}")

        except Exception as e:
            logger.error(f"[auto_migrate] fatal: {e}", exc_info=True)
            report.errors.append(str(e))

    report.log_summary()
    return report


__all__ = ["run", "MigrationReport"]
