from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from core.lib.database import get_db
from core import Aras
from core.response import ok
from .models import HandoffRun, TemplateAnnotation, StyleOverride


from core.auth.service import require_admin

dev_api_router = APIRouter(tags=["Developer Templates"], dependencies=[Depends(require_admin)])

@dev_api_router.get("/dev_template_trees")
def get_template_tree(template_name: str, db: Session = Depends(get_db)):
    # Return the latest tree_json for a template
    ann = db.query(TemplateAnnotation).filter(
        TemplateAnnotation.template_name == template_name,
        TemplateAnnotation.tree_json.is_not(None)
    ).order_by(TemplateAnnotation.id.desc()).first()
    
    return ok({"tree_json": ann.tree_json if ann else None})


@dev_api_router.post("/dev_template_trees")
def upsert_template_tree(payload: Dict[str, Any], db: Session = Depends(get_db)):
    template_name = payload.get("template_name")
    tree_json = payload.get("tree_json")
    if not template_name:
        raise HTTPException(status_code=400, detail="template_name is required")
        
    # We just create a new record for the tree snapshot
    ann = TemplateAnnotation(
        template_name=template_name,
        tree_json=tree_json,
        author="system",
        node_id="root",
        node_kind="TreeSnapshot",
        status="applied"
    )
    db.add(ann)
    db.commit()
    return ok({"status": "ok"})


@dev_api_router.post("/dev_template_annotations")
def create_annotation(payload: Dict[str, Any], db: Session = Depends(get_db)):
    # Accept the new payload manually just in case auto-generated route lacks support
    # payload { template_name, node_id, node_kind, node_label, breakpoint, comment, status, tree_json? }
    ann = TemplateAnnotation(
        template_name=payload.get("template_name"),
        node_id=payload.get("node_id"),
        node_kind=payload.get("node_kind"),
        node_label=payload.get("node_label"),
        breakpoint=payload.get("breakpoint"),
        comment=payload.get("comment"),
        status=payload.get("status", "pending"),
        tree_json=payload.get("tree_json"),
        author="system"
    )
    db.add(ann)
    db.commit()
    db.refresh(ann)
    return ok(ann.to_dict())


# claude-opus-4-7
# Public read endpoint — no auth — so MainLayout can apply overrides on unauthenticated routes too.
style_public_router = APIRouter(tags=["Style Overrides"])

@style_public_router.get("/style-overrides")
def list_style_overrides_for_route(path: str = "/", db: Session = Depends(get_db)):
    rows = db.query(StyleOverride).all()
    matching = [
        {
            "id": r.id,
            "scope": r.scope,
            "selector": r.selector,
            "label": r.label,
            "css_json": r.css_json or {},
            "text_override": r.text_override,
            "hidden": bool(r.hidden),
        }
        for r in rows
        if r.scope == "global" or (path or "/").startswith(r.scope)
    ]
    return ok(matching)


@dev_api_router.post("/style-overrides")
def upsert_style_override(payload: Dict[str, Any], db: Session = Depends(get_db)):
    scope = (payload.get("scope") or "global").strip()
    selector = (payload.get("selector") or "").strip()
    if not selector:
        raise HTTPException(status_code=400, detail="selector is required")
    row = (
        db.query(StyleOverride)
        .filter(StyleOverride.scope == scope, StyleOverride.selector == selector)
        .first()
    )
    if row is None:
        row = StyleOverride(scope=scope, selector=selector)
        db.add(row)
    if "css_json" in payload:
        row.css_json = payload.get("css_json") or {}
    if "label" in payload:
        row.label = payload.get("label")
    if "text_override" in payload:
        row.text_override = payload.get("text_override")
    if "hidden" in payload:
        row.hidden = bool(payload.get("hidden"))
    db.commit()
    db.refresh(row)
    return ok({
        "id": row.id,
        "scope": row.scope,
        "selector": row.selector,
        "label": row.label,
        "css_json": row.css_json or {},
        "text_override": row.text_override,
        "hidden": bool(row.hidden),
    })


@dev_api_router.delete("/style-overrides/{override_id}")
def delete_style_override(override_id: int, db: Session = Depends(get_db)):
    row = db.query(StyleOverride).filter(StyleOverride.id == override_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    db.delete(row)
    db.commit()
    return ok({"deleted": override_id})


# claude-opus-4-7
@dev_api_router.get("/style-overrides/history")
def style_override_history(path: str = "/", limit: int = 20, db: Session = Depends(get_db)):
    """List recent overrides for a route (most recent first) so the UI can offer undo."""
    rows = (
        db.query(StyleOverride)
        .order_by(StyleOverride.updated_at.desc().nullslast(), StyleOverride.id.desc())
        .limit(limit)
        .all()
    )
    matching = [
        {
            "id": r.id,
            "scope": r.scope,
            "selector": r.selector,
            "label": r.label,
            "css_json": r.css_json or {},
            "hidden": bool(r.hidden),
            "text_override": r.text_override,
            "updated_at": r.updated_at.isoformat() if getattr(r, "updated_at", None) else None,
        }
        for r in rows
        if r.scope == "global" or (path or "/").startswith(r.scope)
    ]
    return ok(matching)


# claude-opus-4-7
# Field DnD reorder — bulk update FieldModel.display_order for a resource.
@dev_api_router.post("/field-reorder")
def reorder_fields(payload: Dict[str, Any], db: Session = Depends(get_db)):
    resource_name = payload.get("resource")
    order_list = payload.get("order")  # list of field names in desired order
    if not resource_name or not isinstance(order_list, list):
        raise HTTPException(status_code=400, detail="resource + order required")
    from core.registry.resource_model import ResourceModel
    from core.registry.field_model import FieldModel
    resource = db.query(ResourceModel).filter(ResourceModel.name == resource_name).first()
    if resource is None:
        raise HTTPException(status_code=404, detail="resource not found")
    fields = db.query(FieldModel).filter(FieldModel.resource_id == resource.id).all()
    by_name = {f.name: f for f in fields}
    for idx, name in enumerate(order_list, start=1):
        f = by_name.get(name)
        if f is not None:
            f.display_order = idx
            f.is_override = True
    db.commit()
    # invalidate UI generator cache for this resource
    try:
        from core.logic.ui_generator import UIGenerator
        UIGenerator._metadata_cache = {k: v for k, v in UIGenerator._metadata_cache.items() if k[0] != resource_name}
    except Exception:
        pass
    return ok({"resource": resource_name, "count": len(order_list)})


# claude-opus-4-7
# AI edit — send selector + computed styles + user instruction to Claude, return a CSS patch.
@dev_api_router.post("/style-overrides/ai")
def ai_style_edit(payload: Dict[str, Any]):
    import os, json as _json
    selector = (payload.get("selector") or "").strip()
    instruction = (payload.get("instruction") or "").strip()
    computed = payload.get("computed") or {}
    tag = payload.get("tag") or "div"
    if not selector or not instruction:
        raise HTTPException(status_code=400, detail="selector + instruction required")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="ANTHROPIC_API_KEY not configured")
    try:
        from anthropic import Anthropic
    except ImportError:
        raise HTTPException(status_code=500, detail="anthropic SDK not installed: pip install anthropic")
    client = Anthropic(api_key=api_key)
    sys = (
        "You are a CSS expert. Given a DOM element's tag, current computed styles, and a user instruction, "
        "return ONLY a JSON object mapping CSS property names (kebab-case) to values. "
        'No prose, no markdown fences. Example: {"color": "#222", "padding": "16px"}. '
        "Use !important sparingly; do not add it unless the change must override existing rules."
    )
    user_msg = (
        f"Element: <{tag}>\nSelector: {selector}\n"
        f"Computed styles: {_json.dumps(computed)}\n\nInstruction: {instruction}\n\nReturn JSON only."
    )
    resp = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=600,
        system=sys,
        messages=[{"role": "user", "content": user_msg}],
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
    # Strip accidental fences
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    try:
        patch = _json.loads(text)
        if not isinstance(patch, dict):
            raise ValueError("not an object")
    except Exception:
        raise HTTPException(status_code=502, detail=f"AI returned non-JSON: {text[:200]}")
    return ok({"selector": selector, "css_json": patch})


from . import views  # noqa: F401
from core.logic.discovery import autodiscover_models

class Dev(Aras.App):
    """
    Advanced Developer Tools for framework maintenance and inspection.
    """
    app_name = "dev"
    app_type = "framework"
    app_label = "Developer Tools"
    description = "Framework inspection, metadata management, and database tools."
    icon = "Terminal"
    have_home = True

    routers = [dev_api_router, style_public_router]

    @staticmethod
    def seed(db: Session):
        from . import seed_templates
        seed_templates.run(db)

    models = [
        Aras.AppModel,
        Aras.ResourceModel,
        Aras.FieldModel,
        Aras.LinkModel,
        Aras.ActivityLog,
        Aras.User,
        Aras.SettingsModel,
        Aras.WidgetModel,
        Aras.DashboardLayoutModel,
    ] + autodiscover_models(__name__, ["models"])

    menu_groups = [
        {
            "label": "Registry",
            "icon": "Database",
            "models": ["core_apps", "core_resources", "core_fields", "core_links"]
        },
        {
            "label": "Audit & Config",
            "icon": "ClipboardList",
            "models": ["core_activity_logs", "core_settings"]
        },
        {
            "label": "Agent Runs",
            "icon": "GitBranch",
            "models": ["dev_handoff_runs"]
        },
        {
            "label": "Templates",
            "icon": "Layout",
            "models": ["dev_template_annotations"]
        }
    ]
