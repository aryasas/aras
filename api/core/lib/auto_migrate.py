import logging
import os
from dataclasses import dataclass, field
from sqlalchemy import inspect as sa_inspect, text
from sqlalchemy.schema import CreateTable
from sqlalchemy import String, Text

logger = logging.getLogger(__name__)

@dataclass
class MigrationReport:
    created_tables:  list[str] = field(default_factory=list)
    added_columns:   list[str] = field(default_factory=list)
    added_indexes:   list[str] = field(default_factory=list)
    widened_columns: list[str] = field(default_factory=list)
    errors:          list[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return any([
            self.created_tables, self.added_columns, self.added_indexes,
            self.widened_columns, self.errors
        ])

    def log_summary(self):
        if not self.has_changes():
            return
            
        if self.created_tables:
            print(f"[auto_migrate] created tables: {self.created_tables}")
        if self.added_columns:
            print(f"[auto_migrate] added columns: {self.added_columns}")
        if self.added_indexes:
            print(f"[auto_migrate] added indexes: {self.added_indexes}")
        if self.widened_columns:
            print(f"[auto_migrate] widened/modified: {self.widened_columns}")
        if self.errors:
            print(f"[auto_migrate] errors: {self.errors}")

def _quote(name: str) -> str:
    return f"`{name}`"

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

def run(engine, metadata) -> MigrationReport:
    report = MigrationReport()
    
    try:
        insp = sa_inspect(engine)
        dialect = engine.dialect
        
        db_tables = set(insp.get_table_names())
        model_tables = set(metadata.tables.keys())

        # 1. Create missing tables (as backup to create_all)
        for tname in sorted(model_tables - db_tables):
            try:
                tbl = metadata.tables[tname]
                tbl.create(bind=engine)
                report.created_tables.append(tname)
            except Exception as e:
                report.errors.append(f"create {tname}: {e}")

        # 2. Diff existing tables
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
                              .replace(" ", ""))
                        return s
                        
                    if _norm(target_type) != _norm(live_type) \
                       and not _norm(live_type).startswith(_norm(target_type)) \
                       and not _norm(target_type).startswith(_norm(live_type)):
                        
                        nullable_sql = "" if mcol.nullable else " NOT NULL"
                        default = _safe_default_sql(mcol)
                        default_sql = f" DEFAULT {default}" if default is not None else ""
                        
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
