"""
AI Context Bridge — writes live page/resource context to disk so Claude Code (CLI,
subscription, no API key) can read and act on it directly.

A page calls POST /ai-context/{resource}; the server resolves the model, serializes
its schema + a data sample to .aras/context/<resource>.json, and updates a manifest
the CLI watches. The CLI reads files off disk — no network, no token.
"""
import os
import json
import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..lib.database import get_db
from ..auth.service import require_admin
from ..response import ok

router = APIRouter(tags=["AI Context Bridge"], dependencies=[Depends(require_admin)])

# Repo-root-relative; CLI looks here. Kept out of api/ so it sits at project root.
CONTEXT_DIR = os.path.join(os.getcwd(), ".aras", "context")
MANIFEST_PATH = os.path.join(os.getcwd(), ".aras", "context", "_manifest.json")


# claude-opus-4-8
def _resolve_model(resource_name: str):
    """Mirror registry.get_resource_metadata resolution: clean-path, then registry, then core."""
    from ..base.model import Model
    from ..base.app import App

    path = resource_name if resource_name.startswith("/") else f"/{resource_name}"
    path = path.replace("_", "-")

    for app_cls in App._registry.values():
        for model in app_cls.models:
            if hasattr(model, "__tablename__") and app_cls._get_clean_path(model.__tablename__) == path:
                return model
    tablename = resource_name.split("/")[-1] if "/" in resource_name else resource_name
    model = Model._registry.get(tablename)
    if model:
        return model
    from ..aras import Aras
    for m in [Aras.User, Aras.Role, Aras.Permission, Aras.ActivityLog, Aras.SettingsModel,
              Aras.AppModel, Aras.ResourceModel, Aras.FieldModel, Aras.LinkModel,
              Aras.TranslationModel, Aras.WidgetModel, Aras.DashboardLayoutModel]:
        if m.__tablename__ == tablename:
            return m
    return None


# claude-opus-4-8
def _serialize_columns(model) -> List[dict]:
    cols = []
    for col in model.__table__.columns:
        fks = [f"{fk.column.table.name}.{fk.column.name}" for fk in col.foreign_keys]
        cols.append({
            "name": col.name,
            "type": str(col.type),
            "nullable": col.nullable,
            "primary_key": col.primary_key,
            "foreign_key": fks[0] if fks else None,
        })
    return cols


# claude-opus-4-8
def _serialize_row(row, columns: List[str]) -> dict:
    out = {}
    for c in columns:
        v = getattr(row, c, None)
        if hasattr(v, "isoformat"):
            v = v.isoformat()
        elif not isinstance(v, (str, int, float, bool, type(None))):
            v = str(v)
        out[c] = v
    return out


# claude-opus-4-8
def _write_manifest():
    """Rebuild the manifest index of all written context files."""
    entries = []
    if os.path.isdir(CONTEXT_DIR):
        for fn in sorted(os.listdir(CONTEXT_DIR)):
            if fn.endswith(".json") and not fn.startswith("_"):
                fp = os.path.join(CONTEXT_DIR, fn)
                entries.append({
                    "resource": fn[:-5],
                    "file": f".aras/context/{fn}",
                    "updated_at": datetime.datetime.fromtimestamp(os.path.getmtime(fp)).isoformat(),
                })
    with open(MANIFEST_PATH, "w") as f:
        json.dump({"generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "resources": entries}, f, indent=2)


# claude-opus-4-8
@router.post("/ai-context/{resource_name:path}")
def export_context(
    resource_name: str,
    db: Session = Depends(get_db),
    note: Optional[str] = Query(None, description="Free-text note for the AI to act on"),
    sample: int = Query(20, le=200),
):
    """Write a resource's live schema + data sample to .aras/context/<resource>.json for the CLI."""
    model = _resolve_model(resource_name)
    if not model:
        raise HTTPException(status_code=404, detail=f"resource '{resource_name}' not found")

    columns = _serialize_columns(model)
    col_names = [c["name"] for c in columns]
    pk = next((c["name"] for c in columns if c["primary_key"]), "id")

    try:
        rows = db.query(model).order_by(getattr(model, pk).desc()).limit(sample).all()
        total = db.query(model).count()
    except Exception:
        rows, total = [], 0

    payload = {
        "resource": resource_name,
        "table": model.__tablename__,
        "label": getattr(model, "__aras_meta__", {}).get("label", model.__tablename__) if hasattr(model, "__aras_meta__") else model.__tablename__,
        "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "note": note,
        "schema": {"columns": columns},
        "data": {
            "total_rows": total,
            "sample_size": len(rows),
            "rows": [_serialize_row(r, col_names) for r in rows],
        },
        "hint_for_ai": (
            "This file is the live context of an Aras page. Schema lists every column "
            "(types, nullability, FKs). Data is a recent sample. Use it to answer questions "
            "or generate code against this resource. The user's intent is in 'note'."
        ),
    }

    os.makedirs(CONTEXT_DIR, exist_ok=True)
    safe = resource_name.strip("/").replace("/", "__")
    out_path = os.path.join(CONTEXT_DIR, f"{safe}.json")
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    _write_manifest()

    return ok({
        "written": f".aras/context/{safe}.json",
        "table": model.__tablename__,
        "columns": len(columns),
        "sample_rows": len(rows),
        "total_rows": total,
        "cli_hint": f"In Claude Code: read .aras/context/{safe}.json — it has this page's schema + data.",
    })


# claude-opus-4-8
@router.get("/ai-context")
def list_context():
    """List all exported context files (the manifest)."""
    if not os.path.exists(MANIFEST_PATH):
        return ok({"resources": []})
    with open(MANIFEST_PATH) as f:
        return ok(json.load(f))
