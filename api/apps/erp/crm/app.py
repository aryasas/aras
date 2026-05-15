from ..app import ERP
from .models import Customer, Contact, Lead, Pipeline, Stage, Activity

class CRM(ERP):
    app_name = "erp_crm"
    app_label = "CRM"
    icon = "Users"
    
    models = [Customer, Contact, Lead, Pipeline, Stage, Activity]

    
    menu_groups = [
        {
            "label": "Sales Force",
            "icon": "Users",
            "models": ["erp_crm_leads", "erp_crm_pipelines"]
        },
        {
            "label": "Master Data",
            "icon": "Database",
            "models": ["erp_crm_customers", "erp_crm_contacts"]
        }
    ]

