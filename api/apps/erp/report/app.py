from ..app import ERP
from .models import Report
from . import views # Trigger view registration

class ReportApp(ERP):
    app_name = "erp_report"
    app_label = "Reports"
    icon = "FileBarChart"

    models = [Report]

    menu_groups = [
        {
            "label": "All Reports",
            "icon": "FileText",
            "models": ["erp_report_reports"]
        }
    ]
