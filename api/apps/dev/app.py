from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from core.lib.database import get_db
from core import Aras
from .models import HandoffRun, TemplateAnnotation


from core.auth.service import require_admin

dev_api_router = APIRouter(prefix="/dev", tags=["Developer Templates"], dependencies=[Depends(require_admin)])

@dev_api_router.get("/dev_template_trees")
def get_template_tree(template_name: str, db: Session = Depends(get_db)):
    # Return the latest tree_json for a template
    ann = db.query(TemplateAnnotation).filter(
        TemplateAnnotation.template_name == template_name,
        TemplateAnnotation.tree_json.is_not(None)
    ).order_by(TemplateAnnotation.id.desc()).first()
    if not ann or not ann.tree_json:
        return {"tree_json": None}
    return {"tree_json": ann.tree_json}


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
    return {"status": "ok"}


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
    return ann.to_dict()


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

    routers = [dev_api_router]

    models = [
        Aras.AppModel,
        Aras.ResourceModel,
        Aras.FieldModel,
        Aras.LinkModel,
        Aras.ActivityLog,
        Aras.User,
        Aras.ArasSetting,
        Aras.WidgetModel,
        Aras.DashboardLayoutModel,
    ] + autodiscover_models(__name__, ["models"])

    menu_groups = [
        {
            "label": "Registry",
            "icon": "Database",
            "models": ["aras_apps", "aras_resources", "aras_fields", "aras_links"]
        },
        {
            "label": "Audit & Config",
            "icon": "ClipboardList",
            "models": ["aras_activity_logs", "sys_settings"]
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
