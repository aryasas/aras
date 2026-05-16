from core import Aras
from .models import HandoffRun


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
        HandoffRun,
    ]

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
        }
    ]
