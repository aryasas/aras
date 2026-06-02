from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from core.lib.database import get_db
from core.response import ok
from .models import TemplateAnnotation, StyleOverride

dev_ui_router = APIRouter(tags=["Developer UI Tools"])

# Public read endpoint — no auth — so MainLayout can apply overrides on unauthenticated routes too.
style_public_router = APIRouter(tags=["Style Overrides"])

class TemplateTreeRequest(BaseModel):
    template_name: str
    tree_json: Optional[Dict[str, Any]] = None

@dev_ui_router.get("/dev/template-trees")
def get_template_tree(template_name: str, db: Session = Depends(get_db)):
    # Return the latest tree_json for a template
    ann = db.query(TemplateAnnotation).filter(
        TemplateAnnotation.template_name == template_name,
        TemplateAnnotation.tree_json.is_not(None)
    ).order_by(TemplateAnnotation.id.desc()).first()
    
    return ok({"tree_json": ann.tree_json if ann else None})

@dev_ui_router.post("/dev/template-trees")
def upsert_template_tree(payload: TemplateTreeRequest, db: Session = Depends(get_db)):
    # We just create a new record for the tree snapshot
    ann = TemplateAnnotation(
        template_name=payload.template_name,
        tree_json=payload.tree_json,
        author="system",
        node_id="root",
        node_kind="TreeSnapshot",
        status="applied"
    )
    db.add(ann)
    db.commit()
    return ok({"status": "ok"})

class TemplateAnnotationRequest(BaseModel):
    template_name: str
    node_id: str
    node_kind: str
    node_label: Optional[str] = None
    breakpoint: Optional[bool] = False
    comment: Optional[str] = None
    status: Optional[str] = "pending"
    tree_json: Optional[Dict[str, Any]] = None

@dev_ui_router.post("/dev/template-annotations")
def create_annotation(payload: TemplateAnnotationRequest, db: Session = Depends(get_db)):
    ann = TemplateAnnotation(
        template_name=payload.template_name,
        node_id=payload.node_id,
        node_kind=payload.node_kind,
        node_label=payload.node_label,
        breakpoint=payload.breakpoint,
        comment=payload.comment,
        status=payload.status,
        tree_json=payload.tree_json,
        author="system"
    )
    db.add(ann)
    db.commit()
    db.refresh(ann)
    return ok(ann.to_dict())

@style_public_router.get("/dev/style-overrides")
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

class StyleOverrideRequest(BaseModel):
    scope: Optional[str] = "global"
    selector: str
    css_json: Optional[Dict[str, Any]] = None
    label: Optional[str] = None
    text_override: Optional[str] = None
    hidden: Optional[bool] = False

@dev_ui_router.post("/dev/style-overrides")
def upsert_style_override(payload: StyleOverrideRequest, db: Session = Depends(get_db)):
    scope = payload.scope.strip()
    selector = payload.selector.strip()
    row = (
        db.query(StyleOverride)
        .filter(StyleOverride.scope == scope, StyleOverride.selector == selector)
        .first()
    )
    if row is None:
        row = StyleOverride(scope=scope, selector=selector)
        db.add(row)
    if payload.css_json is not None:
        row.css_json = payload.css_json or {}
    if payload.label is not None:
        row.label = payload.label
    if payload.text_override is not None:
        row.text_override = payload.text_override
    if payload.hidden is not None:
        row.hidden = payload.hidden
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

@dev_ui_router.delete("/dev/style-overrides/{override_id}")
def delete_style_override(override_id: int, db: Session = Depends(get_db)):
    row = db.query(StyleOverride).filter(StyleOverride.id == override_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    db.delete(row)
    db.commit()
    return ok({"deleted": override_id})

@dev_ui_router.get("/dev/style-overrides/history")
def style_override_history(path: str = "/", limit: int = 20, db: Session = Depends(get_db)):
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
            "updated_at": r.updated_at.isoformat() if hasattr(r.updated_at, 'isoformat') else None,
        }
        for r in rows
        if r.scope == "global" or (path or "/").startswith(r.scope)
    ]
    return ok(matching)

class FieldReorderRequest(BaseModel):
    resource: str
    order: List[str]

@dev_ui_router.post("/dev/field-reorder")
def reorder_fields(payload: FieldReorderRequest, db: Session = Depends(get_db)):
    from core.registry.resource_model import ResourceModel
    from core.registry.field_model import FieldModel
    resource = db.query(ResourceModel).filter(ResourceModel.name == payload.resource).first()
    if resource is None:
        raise HTTPException(status_code=404, detail="resource not found")
    fields = db.query(FieldModel).filter(FieldModel.resource_id == resource.id).all()
    by_name = {f.name: f for f in fields}
    for idx, name in enumerate(payload.order, start=1):
        f = by_name.get(name)
        if f is not None:
            f.display_order = idx
            f.is_override = True
    db.commit()
    # invalidate UI generator cache for this resource
    try:
        from core.logic.ui_generator import UIGenerator
        UIGenerator._metadata_cache = {k: v for k, v in UIGenerator._metadata_cache.items() if k[0] != payload.resource}
    except Exception:
        pass
    return ok({"resource": payload.resource, "count": len(payload.order)})

class AIStyleEditRequest(BaseModel):
    selector: str
    instruction: str
    computed: Optional[Dict[str, Any]] = None
    tag: Optional[str] = "div"

@dev_ui_router.post("/dev/style-overrides/ai")
def ai_style_edit(payload: AIStyleEditRequest):
    import os, json as _json
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
        f"Element: <{payload.tag}>\nSelector: {payload.selector}\n"
        f"Computed styles: {_json.dumps(payload.computed or {})}\n\nInstruction: {payload.instruction}\n\nReturn JSON only."
    )
    resp = client.messages.create(
        model="claude-3-5-sonnet-20241022",
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
    return ok({"selector": payload.selector, "css_json": patch})

class AILayoutRequest(BaseModel):
    resource: str
    instruction: str
    current_layout: Optional[List[Any]] = None

# claude-sonnet-4-6
@dev_ui_router.post("/dev/layout/ai")
def ai_layout_generate(payload: AILayoutRequest, db: Session = Depends(get_db)):
    import os, json as _json
    from core.registry.resource_model import ResourceModel
    from core.registry.field_model import FieldModel

    # Fetch resource + its fields
    resource = db.query(ResourceModel).filter(ResourceModel.name == payload.resource).first()
    if resource is None:
        raise HTTPException(status_code=404, detail=f"resource '{payload.resource}' not found")
    fields = db.query(FieldModel).filter(FieldModel.resource_id == resource.id).order_by(FieldModel.display_order).all()
    field_names = [f.name for f in fields if f.name not in ("id", "created_at", "updated_at")]

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="ANTHROPIC_API_KEY not configured")
    try:
        from anthropic import Anthropic
    except ImportError:
        raise HTTPException(status_code=500, detail="anthropic SDK not installed: pip install anthropic")

    client = Anthropic(api_key=api_key)

    schema_doc = """
layout_json is a JSON array of layout blocks. Each block is one of:

1. Section block:
   {"type": "section", "title": "string", "fields": ["field_name", ...], "foldable": bool, "default_folded": bool}

2. Tab container block (groups multiple tabs):
   {"type": "tabs", "tabs": [
     {"type": "tab", "title": "string", "fields": ["field_name", ...], "foldable": bool, "default_folded": bool},
     ...
   ]}

3. A field entry in "fields" is either a plain string (field name) or an object:
   {"field": "field_name", "columns": 2}   (columns = 1 or 2, for two-column layout within a section)

Rules:
- Every field name used MUST come from the provided field list.
- Do not invent field names.
- The top-level result MUST be a JSON array (not an object).
- Include every field from the list — do not drop any.
- "foldable" and "default_folded" default to false if not needed.
"""

    current_str = _json.dumps(payload.current_layout) if payload.current_layout else "null (no existing layout)"
    user_msg = (
        f"Resource: {payload.resource}\n"
        f"Available fields: {_json.dumps(field_names)}\n"
        f"Current layout: {current_str}\n\n"
        f"Instruction: {payload.instruction}\n\n"
        f"Return ONLY a valid layout_json array. No prose, no markdown fences."
    )

    resp = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1200,
        system=f"You are a form layout expert. {schema_doc}\nReturn ONLY the JSON array — no explanation.",
        messages=[{"role": "user", "content": user_msg}],
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()

    try:
        layout = _json.loads(text)
        if not isinstance(layout, list):
            raise ValueError("layout_json must be an array")
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"AI returned invalid JSON: {exc} — raw: {text[:300]}")

    # Validate: all referenced field names exist
    valid_set = set(field_names)
    def _collect_field_names(blocks):
        names = []
        for block in blocks:
            for f in block.get("fields", []):
                names.append(f if isinstance(f, str) else f.get("field", ""))
            for tab in block.get("tabs", []):
                for f in tab.get("fields", []):
                    names.append(f if isinstance(f, str) else f.get("field", ""))
        return names

    referenced = _collect_field_names(layout)
    bad = [n for n in referenced if n and n not in valid_set]
    if bad:
        raise HTTPException(status_code=422, detail=f"AI referenced unknown fields: {bad}")

    return ok({"layout_json": layout, "applied": False})
