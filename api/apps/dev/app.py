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

    @classmethod
    def register_services(cls):
        from core.service_registry import ServiceRegistry
        from .models import HandoffRun, TemplateAnnotation
        ServiceRegistry.register("HandoffRun", HandoffRun)
        ServiceRegistry.register("TemplateAnnotation", TemplateAnnotation)

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
        {"label": "Inspect", "icon": "Search", "pages": [
            {"name": "dev_overview", "label": "Overview", "path": "/admin/dev", "icon": "LayoutDashboard", "component": "dev.overview"},
            {"name": "dev_schema", "label": "Schema", "path": "/admin/dev/schema", "icon": "GitCompare", "component": "dev.schema"},
            {"name": "dev_models", "label": "Models", "path": "/admin/dev/models", "icon": "Boxes", "component": "dev.models"},
            {"name": "dev_routes", "label": "Routes", "path": "/admin/dev/routes-debug", "icon": "Route", "component": "dev.routes"},
            {"name": "dev_timeline", "label": "Timeline", "path": "/admin/dev/timeline", "icon": "Activity", "component": "dev.timeline"},
        ]},
        {"label": "Operate", "icon": "Wrench", "pages": [
            {"name": "dev_workbench", "label": "Workbench", "path": "/admin/dev/workbench", "icon": "Wrench", "component": "dev.workbench"},
            {"name": "dev_cache", "label": "Cache", "path": "/admin/dev/cache", "icon": "Trash2", "component": "dev.cache"},
            {"name": "dev_commands", "label": "Commands", "path": "/admin/dev/commands", "icon": "Command", "component": "dev.commands"},
            {"name": "dev_sql", "label": "SQL Runner", "path": "/admin/dev/sql", "icon": "Terminal", "component": "dev.sql"},
            {"name": "dev_access", "label": "Access", "path": "/admin/dev/access", "icon": "Shield", "component": "dev.access"},
        ]},
        {"label": "Build & Test", "icon": "Code", "pages": [
            {"name": "dev_testlab", "label": "Test Lab", "path": "/admin/dev/test-lab", "icon": "Zap", "component": "dev.testlab"},
            {"name": "dev_scaffold", "label": "Scaffold", "path": "/admin/dev/scaffold", "icon": "Code2", "component": "dev.scaffold"},
            {"name": "dev_mocks", "label": "Mocks", "path": "/admin/dev/mocks", "icon": "Globe", "component": "dev.mocks"},
            {"name": "dev_templatebuilder", "label": "Template Builder", "path": "/admin/dev/template-builder", "icon": "FileCode", "component": "dev.templatebuilder"},
            {"name": "dev_apihelp", "label": "API Help", "path": "/admin/dev/api-help", "icon": "Code2", "component": "dev.apihelp"},
            {"name": "dev_help", "label": "Dev Help", "path": "/admin/dev/help", "icon": "HelpCircle", "component": "dev.help"},
            {"name": "dev_handoff", "label": "Handoff", "path": "/admin/dev/handoff", "icon": "GitBranch", "component": "dev.handoff"},
            {"name": "dev_logs", "label": "Logs", "path": "/admin/dev/logs", "icon": "AlertTriangle", "component": "dev.logs"},
        ]},
    ]
