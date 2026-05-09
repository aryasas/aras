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


def _schema_hash(meta) -> str:
    """Stable hash of SQLAlchemy metadata — table+column names and types."""
    import hashlib, json
    sig = {}
    for tname, tbl in sorted(meta.tables.items()):
        sig[tname] = {c.name: str(c.type) for c in tbl.columns}
    return hashlib.sha256(json.dumps(sig, sort_keys=True).encode()).hexdigest()


def _hash_path(flask_app) -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(flask_app.root_path)))
    return os.path.join(root, "instance", "schema_hash.json")


def _read_stored_hash(flask_app) -> str | None:
    try:
        import json
        with open(_hash_path(flask_app)) as f:
            return json.load(f).get("hash")
    except Exception:
        return None


def _write_hash(flask_app, h: str) -> None:
    import json
    try:
        path = _hash_path(flask_app)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump({"hash": h}, f)
    except Exception:
        pass


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

def run(flask_app, *, autoload_had_errors: bool = False, skip_drops: bool = False) -> MigrationReport:
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
        # Build an isolated DDL engine with NullPool so each statement opens
        # and closes its own connection — this avoids self-deadlock where a
        # pooled connection from an earlier boot step (autoload, sidebar build)
        # holds an idle InnoDB snapshot transaction that blocks ALTER TABLE
        # on the same metadata.
        from sqlalchemy import create_engine
        from sqlalchemy.pool import NullPool

        # Drop any session-level transaction the shared engine may hold.
        # We must COMMIT (not just rollback) any active read transaction —
        # under InnoDB REPEATABLE-READ a SELECT opens a snapshot transaction
        # that holds metadata locks on every table it touched, blocking ALTER.
        try:
            db.session.commit()
        except Exception:
            try:
                db.session.rollback()
            except Exception:
                pass
        try:
            db.session.close()
            db.session.remove()
        except Exception:
            pass
        try:
            db.engine.dispose()
        except Exception:
            pass

        ddl_uri = db.engine.url.render_as_string(hide_password=False)
        engine  = create_engine(ddl_uri, poolclass=NullPool, future=True)

        # Self-deadlock guard: kill any other connections from THIS process
        # that hold idle InnoDB snapshot transactions on our schema. They
        # would otherwise block our ALTER TABLE statements.
        # Tell Flask-SQLAlchemy to fully close & forget any session/connection
        # held under this app context, so the post-DDL teardown does not try
        # to rollback a connection we killed below.
        try:
            db.session.close()
        except Exception:
            pass
        try:
            db.session.remove()
        except Exception:
            pass
        try:
            db.engine.dispose(close=True)
        except Exception:
            pass

        # Now KILL any other server-side connections from our process that
        # hold idle InnoDB snapshots and would block our ALTER statements.
        try:
            from sqlalchemy import text
            with engine.begin() as _kc:
                my_id = _kc.execute(text("SELECT CONNECTION_ID()")).scalar()
                rows = _kc.execute(text(
                    "SELECT id FROM information_schema.processlist "
                    "WHERE db = DATABASE() AND id <> :me AND command = 'Sleep'"
                ), {"me": my_id}).fetchall()
                for (other_id,) in rows:
                    try:
                        _kc.execute(text(f"KILL {int(other_id)}"))
                    except Exception:
                        pass
        except Exception as _kill_err:
            logger.warning(f"[auto_migrate] preflight kill failed: {_kill_err}")

        # Invalidate again so any reconnect after KILL gets a fresh handle,
        # and Flask-SQLAlchemy teardown can no-op cleanly.
        try:
            db.engine.dispose(close=True)
        except Exception:
            pass

        try:
            insp   = sa_inspect(engine)
            meta   = db.metadata
            dialect = engine.dialect

            # Skip the full diff if schema hasn't changed since last successful run.
            # The early pass (skip_drops=True) is cheap — let it through to catch
            # newly added core tables. Only skip on the late pass.
            if not skip_drops:
                current_hash = _schema_hash(meta)
                stored_hash  = _read_stored_hash(flask_app)
                if current_hash == stored_hash:
                    logger.info("[auto_migrate] schema unchanged — skipping diff")
                    report.log_summary()
                    return report

            db_tables = set(insp.get_table_names())
            model_tables = set(meta.tables.keys())

            allow_drop = _allow_drop() and not skip_drops
            if skip_drops:
                logger.info("[auto_migrate] skip_drops=True — destructive ops disabled this pass")
            _backup_done = {"v": False}

            def _ensure_backup():
                """Run a DB backup once, on first attempted drop. Aborts the
                drop (returns False) if the backup fails — better to skip a
                drop than lose data."""
                if _backup_done["v"]:
                    return True
                _backup_done["v"] = True
                try:
                    from arasCore.lib.services.backup import run_backup
                    path = run_backup(flask_app, label="pre_auto_migrate")
                    logger.warning(f"[auto_migrate] pre-drop backup: {path}")
                    return True
                except Exception as e:
                    logger.error(f"[auto_migrate] backup FAILED — aborting drops: {e}")
                    report.errors.append(f"backup failed, drops aborted: {e}")
                    return False

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
                    else:
                        # Generic type-drift fix: MODIFY to model type when DB type differs
                        try:
                            target_sql = _column_type_sql(mcol, dialect).upper()
                            live_sql   = str(lcol.get("type")).upper()
                            # Normalise common aliases so we don't churn on equivalents
                            def _norm(s):
                                s = (s.replace("TINYINT(1)", "BOOL")
                                      .replace("BOOLEAN", "BOOL")
                                      .replace("TINYINT", "BOOL")
                                      .replace("INTEGER", "INT")
                                      .replace("NUMERIC", "DECIMAL")
                                      .replace("LONGTEXT", "JSON")
                                      .replace(" ", ""))
                                return s
                            if _norm(target_sql) != _norm(live_sql)                                and not _norm(live_sql).startswith(_norm(target_sql))                                and not _norm(target_sql).startswith(_norm(live_sql)):
                                from sqlalchemy import text
                                nullable_sql = "" if mcol.nullable else " NOT NULL"
                                default = _safe_default_sql(mcol)
                                default_sql = f" DEFAULT {default}" if default is not None else ""
                                sql = f"ALTER TABLE {_quote(tname)} MODIFY {_quote(cname)} {target_sql}{default_sql}{nullable_sql}"
                                with engine.begin() as conn:
                                    conn.execute(text(sql))
                                report.widened_columns.append(f"{tname}.{cname} type {live_sql}→{target_sql}")
                        except Exception as e:
                            report.errors.append(f"modify type {tname}.{cname}: {e}")

                # drop columns (gated)
                drop_cols = set(live_cols) - set(model_cols)
                if drop_cols and not allow_drop:
                    for cname in sorted(drop_cols):
                        report.skipped_unsafe.append(f"DROP COLUMN {tname}.{cname}")
                elif drop_cols:
                    if not _ensure_backup():
                        for cname in sorted(drop_cols):
                            report.skipped_unsafe.append(f"DROP COLUMN {tname}.{cname} (backup failed)")
                        continue
                    from sqlalchemy import text
                    with engine.begin() as conn:
                        try:
                            conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
                        except Exception:
                            pass
                        for cname in sorted(drop_cols):
                            label = f"{tname}.{cname}"
                            try:
                                conn.execute(text(f"ALTER TABLE {_quote(tname)} DROP COLUMN {_quote(cname)}"))
                                report.dropped_columns.append(label)
                            except Exception as e:
                                report.errors.append(f"drop {label}: {e}")
                        try:
                            conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
                        except Exception:
                            pass

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
            drop_targets = [
                t for t in sorted(db_tables - model_tables)
                if not t.startswith("alembic_")
            ]
            if drop_targets and not allow_drop:
                if not skip_drops:
                    for tname in drop_targets:
                        report.skipped_unsafe.append(f"DROP TABLE {tname}")
            elif drop_targets:
                if not _ensure_backup():
                    for tname in drop_targets:
                        report.skipped_unsafe.append(f"DROP TABLE {tname} (backup failed)")
                    drop_targets = []
                from sqlalchemy import text
                # Disable FK checks for the duration so drops succeed regardless of order
                with engine.begin() as conn:
                    try:
                        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
                    except Exception:
                        pass
                    for tname in drop_targets:
                        try:
                            conn.execute(text(f"DROP TABLE {_quote(tname)}"))
                            report.dropped_tables.append(tname)
                        except Exception as e:
                            report.errors.append(f"drop table {tname}: {e}")
                    try:
                        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
                    except Exception:
                        pass

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
        finally:
            try:
                engine.dispose()
            except Exception:
                pass
            # Clear the shared pool — its cached fairies may point at dbapi
            # handles we KILLed above. Without this, the next query (or the
            # app_context teardown rollback) raises "Server has gone away".
            try:
                db.session.remove()
            except Exception:
                pass
            try:
                db.engine.dispose(close=True)
            except Exception:
                pass

    report.log_summary()
    # Persist hash so next boot skips the diff when schema is unchanged.
    if not skip_drops and not report.errors:
        try:
            from arasCore.lib.core.extensions import db as _db
            with flask_app.app_context():
                _write_hash(flask_app, _schema_hash(_db.metadata))
        except Exception:
            pass
    return report


__all__ = ["run", "MigrationReport"]
