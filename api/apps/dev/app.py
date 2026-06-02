from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from core.lib.database import get_db
from core import Aras
from core.response import ok
from core.auth.service import require_admin

# Modularized endpoint routers
from .metrics_router import dev_metrics_router, record_request, error_log_entries
from .db_router import dev_db_router
from .ui_router import dev_ui_router, style_public_router
from .dev_router import dev_general_router

# Core Dev router for template logic and other misc tools
dev_api_router = APIRouter(tags=["Developer Core"], dependencies=[Depends(require_admin)])

@dev_api_router.get("/dev/errors", response_model=List[Dict[str, Any]])
def get_errors():
    """Returns the last 50 error log entries."""
    return list(error_log_entries)[-50:]

@dev_api_router.delete("/dev/errors")
def clear_errors():
    """Clears all error log entries."""
    error_log_entries.clear()
    return ok({"message": "Error log cleared"})

# claude-sonnet-4-6
@dev_api_router.get("/dev/errors/tail", response_model=List[Dict[str, Any]])
def tail_errors(after: Optional[float] = Query(None)):
    """Returns error entries with ts > after for incremental polling."""
    entries = list(error_log_entries)
    if after is not None:
        entries = [e for e in entries if e.get("ts", 0) > after]
    return entries

@dev_api_router.get("/dev/cause-error")
def cause_error():
    """Temporary endpoint to cause an error for testing."""
    raise HTTPException(status_code=418, detail="I'm a teapot - a test error!")


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

    # Combine all modular routers
    routers = [
        dev_api_router,
        dev_metrics_router,
        dev_db_router,
        dev_ui_router,
        dev_general_router,
        style_public_router
    ]

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
