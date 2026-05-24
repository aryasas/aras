from core import Aras
from .models import Lead, Pipeline, Stage, Activity

class CRM(Aras.App):
    app_name = "crm"
    table_prefix = "erp_crm"
    app_label = "CRM"
    icon = "Users"
    
    models = [Lead, Pipeline, Stage, Activity]

    
    menu_groups = [
        {
            "label": "Sales Force",
            "icon": "Users",
            "models": ["erp_crm_leads", "erp_crm_pipelines"]
        },
        {
            "label": "Master Data",
            "icon": "Database",
            "models": []
        }
    ]

