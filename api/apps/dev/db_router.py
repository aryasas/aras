from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from sqlalchemy import text, inspect
import time as _time
import os as _os # Used by alembic import

from core.lib.database import get_db
from core.response import ok
from core import Aras # For Aras.get_all_app_models in schema-diff and Aras.Model._registry

dev_db_router = APIRouter(tags=["Developer Database Tools"])

class SQLQueryRequest(BaseModel):
    sql: str
    limit: Optional[int] = 100

@dev_db_router.post("/dev/sql")
def run_sql_query(payload: SQLQueryRequest, db: Session = Depends(get_db)):
    """Read-only SQL console. Only SELECT/SHOW/EXPLAIN/PRAGMA permitted."""
    sql = payload.sql.strip().rstrip(";")
    limit = payload.limit
    if not sql:
        raise HTTPException(status_code=400, detail="empty query")
    lowered = sql.lower()
    allowed_prefixes = ("select ", "with ", "show ", "explain ", "pragma ", "describe ")
    if not lowered.startswith(allowed_prefixes):
        raise HTTPException(status_code=400, detail="only read-only queries are allowed")
    # Block dangerous keywords even in WITH/SELECT
    banned = ["insert ", "update ", "delete ", "drop ", "alter ", "truncate ", "create ", "grant ", "revoke "]
    if any(b in lowered for b in banned):
        raise HTTPException(status_code=400, detail="mutation keywords not allowed")
    try:
        t0 = _time.time()
        result = db.execute(text(sql))
        rows = [dict(r._mapping) for r in result.fetchmany(limit)]
        # Convert non-serializable values
        for row in rows:
            for k, v in list(row.items()):
                if hasattr(v, 'isoformat'):
                    row[k] = v.isoformat()
                elif not isinstance(v, (str, int, float, bool, type(None), list, dict)):
                    row[k] = str(v)
        elapsed = round((_time.time() - t0) * 1000, 1)
        cols = list(rows[0].keys()) if rows else []
        return ok({"columns": cols, "rows": rows, "row_count": len(rows), "elapsed_ms": elapsed})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"query failed: {str(e)[:300]}")


@dev_db_router.get("/dev/migrations")
def get_migration_status(db: Session = Depends(get_db)):
    """Returns Alembic migration head vs current revision."""
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        alembic_ini = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "alembic.ini")
        if not _os.path.exists(alembic_ini):
            # try root
            alembic_ini = _os.path.join(_os.getcwd(), "alembic.ini")
        if not _os.path.exists(alembic_ini):
            return ok({"available": False, "reason": "alembic.ini not found"})
        cfg = Config(alembic_ini)
        script = ScriptDirectory.from_config(cfg)
        head = script.get_current_head()
        ctx = MigrationContext.configure(db.connection())
        current = ctx.get_current_revision()
        pending = []
        if head and current and head != current:
            for rev in script.iterate_revisions(head, current):
                pending.append({"revision": rev.revision, "doc": rev.doc or ""})
        return ok({
            "available": True,
            "head": head,
            "current": current,
            "up_to_date": head == current,
            "pending": pending,
        })
    except Exception as e:
        return ok({"available": False, "reason": str(e)[:200]})


@dev_db_router.get("/dev/relations/{resource_name}")
def get_resource_relations(resource_name: str):
    """Returns FK relationships and reverse links for a resource."""
    from core.base.model import Model
    model = Model._registry.get(resource_name)
    if not model:
        # try by tablename
        for m in Model._registry.values():
            if getattr(m, "__tablename__", None) == resource_name:
                model = m
                break
    if not model:
        raise HTTPException(status_code=404, detail="model not found")
    columns = []
    foreign_keys = []
    for col in model.__table__.columns:
        columns.append({
            "name": col.name,
            "type": str(col.type),
            "nullable": col.nullable,
            "primary_key": col.primary_key,
            "default": str(col.default) if col.default is not None else None,
        })
        for fk in col.foreign_keys:
            foreign_keys.append({
                "column": col.name,
                "references_table": fk.column.table.name,
                "references_column": fk.column.name,
            })
    # Reverse relations: who references this table?
    referenced_by = []
    target_table = model.__tablename__
    for m in Model._registry.values():
        if m is model:
            continue
        if not hasattr(m, "__table__"):
            continue
        for col in m.__table__.columns:
            for fk in col.foreign_keys:
                if fk.column.table.name == target_table:
                    referenced_by.append({
                        "from_table": m.__tablename__,
                        "from_column": col.name,
                        "to_column": fk.column.name,
                    })
    return ok({
        "name": resource_name,
        "table": target_table,
        "columns": columns,
        "foreign_keys": foreign_keys,
        "referenced_by": referenced_by,
    })


@dev_db_router.get("/dev/schema-diff")
def get_schema_diff(db: Session = Depends(get_db)):
    """
    Compares SQLAlchemy model schema with the actual database schema.
    Returns a list of dictionaries indicating differences per table.
    """
    inspector = inspect(db.bind)
    results = []

    for model_class in Aras.get_all_app_models(): # Use a helper to get all registered models
        if not hasattr(model_class, "__table__"):
            continue # Skip classes that are not SQLAlchemy models

        model_table_name = model_class.__table__.name
        model_columns = {c.name for c in model_class.__table__.columns}

        db_columns = set()
        table_exists_in_db = inspector.has_table(model_table_name)

        if table_exists_in_db:
            try:
                db_table_info = inspector.get_columns(model_table_name)
                db_columns = {col_info["name"] for col_info in db_table_info}
            except Exception as e:
                results.append({
                    "table": model_table_name,
                    "status": "error",
                    "details": [f"Could not inspect DB table: {str(e)}"]
                })
                continue

        missing_columns = list(model_columns - db_columns)
        extra_columns = list(db_columns - model_columns)

        status_text = "ok"
        details = []

        if not table_exists_in_db:
            status_text = "table_missing"
            details.append("Table does not exist in the database.")
        else:
            if missing_columns:
                status_text = "missing_columns"
                details.append(f"Missing in DB: {', '.join(missing_columns)}")
            if extra_columns:
                if status_text == "missing_columns": # If both missing and extra
                    status_text = "missing_and_extra_columns"
                else:
                    status_text = "extra_columns"
                details.append(f"Extra in DB: {', '.join(extra_columns)}")
        
        results.append({
            "table": model_table_name,
            "status": status_text,
            "details": details
        })
    return ok(results)
