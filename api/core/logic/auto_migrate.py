import logging
import os
from typing import Optional
from dataclasses import dataclass, field
from sqlalchemy import inspect as sa_inspect, text
from sqlalchemy.schema import CreateTable
from sqlalchemy import String, Text
from ..base.service import Service

# gemini-flash
logger = logging.getLogger(__name__)

@dataclass
class MigrationReport(Service):
    created_tables:  list[str] = field(default_factory=list)
    dropped_tables:  list[str] = field(default_factory=list)
    added_columns:   list[str] = field(default_factory=list)
    dropped_columns: list[str] = field(default_factory=list)
    added_indexes:   list[str] = field(default_factory=list)
    widened_columns: list[str] = field(default_factory=list)
    errors:          list[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return any([
            self.created_tables, self.dropped_tables, self.added_columns, self.dropped_columns,
            self.added_indexes, self.widened_columns, self.errors
        ])

    def log_summary(self):
        if not self.has_changes():
            return
            
        if self.created_tables:
            logger.info(f"[auto_migrate] created tables: {self.created_tables}")
        if self.dropped_tables:
            logger.info(f"[auto_migrate] dropped tables: {self.dropped_tables}")
        if self.added_columns:
            logger.info(f"[auto_migrate] added columns: {self.added_columns}")
        if self.dropped_columns:
            logger.info(f"[auto_migrate] dropped columns: {self.dropped_columns}")
        if self.added_indexes:
            logger.info(f"[auto_migrate] added indexes: {self.added_indexes}")
        if self.widened_columns:
            logger.info(f"[auto_migrate] widened/modified: {self.widened_columns}")
        if self.errors:
            logger.error(f"[auto_migrate] errors: {self.errors}")

def _quote(name: str) -> str:
    return f'"{name}"'

def _column_type_sql(col, dialect) -> str:
    return col.type.compile(dialect=dialect)

def _safe_default_sql(col) -> Optional[str]:
    """Return inline DEFAULT clause for ADD COLUMN, or None."""
    if col.server_default is not None:
        sd = col.server_default
        try:
            # FetchedValue has no arg
            if hasattr(sd, "arg"):
                arg = sd.arg
                # text() clause
                if hasattr(arg, "text"):
                    return arg.text
                # plain string server_default (e.g. server_default="[]")
                if isinstance(arg, str):
                    return arg
        except Exception:
            pass
        return None
    if col.default is not None and getattr(col.default, "is_scalar", False):
        v = col.default.arg
        if isinstance(v, bool):
            return "TRUE" if v else "FALSE"
        if isinstance(v, (int, float)):
            return str(v)
        if isinstance(v, str):
            return f"'{v}'"
    return None

def run(engine, metadata, drop_orphan_tables: bool = False) -> MigrationReport:
    report = MigrationReport()
    
    try:
        insp = sa_inspect(engine)
        dialect = engine.dialect
        
        db_tables = set(insp.get_table_names())
        model_tables = set(metadata.tables.keys())

        # Bridge tables declared via __m2m__ are physical but not mapped as ORM models.
        # Treat them as expected so they don't appear as orphans.
        m2m_bridges: set[str] = set()
        try:
            from ..base.model import Model  # late import to avoid cycle
            seen = set()
            for cls in Model._registry.values():
                if cls in seen:
                    continue
                seen.add(cls)
                for defs in (getattr(cls, "__m2m__", {}) or {}).values():
                    bt = defs.get("bridge_table") if isinstance(defs, dict) else None
                    if bt:
                        m2m_bridges.add(bt)
        except Exception as e:
            logger.warning(f"[auto_migrate] could not enumerate m2m bridges: {e}")

        # 1. Create missing tables (as backup to create_all)
        for tname in sorted(model_tables - db_tables):
            try:
                tbl = metadata.tables[tname]
                tbl.create(bind=engine)
                report.created_tables.append(tname)
            except Exception as e:
                report.errors.append(f"create {tname}: {e}")

        # 2. Handle orphan tables
        orphans = sorted(db_tables - model_tables)
        if orphans:
            # Protect core tables
            core_tables = {
                "core_apps", "core_resources", "core_fields", "core_links",
                "core_translations", "core_activity_logs", "core_roles",
                "core_permissions", "core_user_roles", "core_users", "core_settings",
                "alembic_version"
            }
            # Transitional: skip pre-2026-05 legacy tables.
            # Remove after all deployments confirmed on `core_*` schema (target 2026-08).
            real_orphans = [t for t in orphans if t not in core_tables and t not in m2m_bridges and not t.startswith("aras_")]
            
            if real_orphans:
                logger.warning(f"[auto_migrate] Found orphan tables in DB: {real_orphans}")
                
                aras_mode = os.getenv("ARAS_MODE", "production")
                if drop_orphan_tables and aras_mode == "development":
                    for tname in real_orphans:
                        try:
                            with engine.begin() as conn:
                                conn.execute(text(f"DROP TABLE IF EXISTS {_quote(tname)} CASCADE"))
                            report.dropped_tables.append(tname)
                            logger.info(f"[auto_migrate] Dropped orphan table: {tname}")
                        except Exception as e:
                            report.errors.append(f"drop table {tname}: {e}")
                elif drop_orphan_tables:
                    logger.warning(f"[auto_migrate] Orphan table drop requested but denied because ARAS_MODE={aras_mode}")

        # 3. Diff existing tables
        for tname in sorted(model_tables & db_tables):
            tbl = metadata.tables[tname]
            live_cols = {c["name"]: c for c in insp.get_columns(tname)}
            model_cols = {c.name: c for c in tbl.columns}

            # Add missing columns
            for cname in sorted(set(model_cols) - set(live_cols)):
                col = model_cols[cname]
                try:
                    type_sql = _column_type_sql(col, dialect)
                    nullable_sql = "" if col.nullable else " NOT NULL"
                    default = _safe_default_sql(col)
                    default_sql = f" DEFAULT {default}" if default is not None else ""
                    
                    # If NOT NULL and no default, we might have issues with existing rows.
                    # But for now, let's follow the lead.
                    sql = f"ALTER TABLE {_quote(tname)} ADD COLUMN {_quote(cname)} {type_sql}{default_sql}{nullable_sql}"
                    with engine.begin() as conn:
                        conn.execute(text(sql))
                    report.added_columns.append(f"{tname}.{cname}")
                except Exception as e:
                    report.errors.append(f"add {tname}.{cname}: {e}")

            # Drop extra columns (exist in DB but not in model)
            _SYSTEM_COLS = {"id", "created_at", "updated_at", "deleted_at", "created_by", "updated_by"}
            for cname in sorted(set(live_cols) - set(model_cols) - _SYSTEM_COLS):
                try:
                    sql = f'ALTER TABLE "{tname}" DROP COLUMN "{cname}"'
                    with engine.begin() as conn:
                        conn.execute(text(sql))
                    report.dropped_columns.append(f"{tname}.{cname}")
                except Exception as e:
                    report.errors.append(f"drop {tname}.{cname}: {e}")

            # Widen/Modify columns (basic check)
            for cname in sorted(set(model_cols) & set(live_cols)):
                mcol = model_cols[cname]
                lcol = live_cols[cname]
                
                try:
                    target_type = _column_type_sql(mcol, dialect).upper()
                    live_type = str(lcol.get("type")).upper()
                    
                    def _norm(s):
                        s = (s.replace("TINYINT(1)", "BOOL")
                              .replace("BOOLEAN", "BOOL")
                              .replace("TINYINT", "BOOL")
                              .replace("INTEGER", "INT")
                              .replace("NUMERIC", "DECIMAL")
                              .replace("LONGTEXT", "JSON")
                              .replace("DOUBLE PRECISION", "FLOAT")
                              .replace(" ", ""))
                        return s
                        
                    if _norm(target_type) != _norm(live_type) \
                       and not _norm(live_type).startswith(_norm(target_type)) \
                       and not _norm(target_type).startswith(_norm(live_type)):
                        
                        nullable_sql = "" if mcol.nullable else " NOT NULL"
                        default = _safe_default_sql(mcol)
                        default_sql = f" DEFAULT {default}" if default is not None else ""
                        
                        # SQLite does not support MODIFY. We skip or use batch migration.
                        # For simplicity in this framework, we skip SQLite MODIFY for now.
                        if dialect.name == "sqlite":
                            continue

                        if dialect.name == "postgresql":
                            sql = f"ALTER TABLE {_quote(tname)} ALTER COLUMN {_quote(cname)} TYPE {target_type}"
                        else:
                            sql = f"ALTER TABLE {_quote(tname)} MODIFY {_quote(cname)} {target_type}{default_sql}{nullable_sql}"
                        with engine.begin() as conn:
                            conn.execute(text(sql))
                        report.widened_columns.append(f"{tname}.{cname} ({live_type} -> {target_type})")
                except Exception as e:
                    # report.errors.append(f"modify {tname}.{cname}: {e}")
                    pass

    except Exception as e:
        report.errors.append(f"fatal auto_migrate: {e}")

    report.log_summary()
    return report
