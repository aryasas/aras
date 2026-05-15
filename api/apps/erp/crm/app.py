from core import Aras
from .models import Customer, Contact
from . import views # Trigger view registration

class CrmApp(Aras.App):
    app_name = "erp_crm"
    parent_name = "erp"
    app_label = "CRM"
    icon = "Users"
    
    models = [Customer, Contact]
    
    menu_groups = [
        {
            "label": "Customers",
            "icon": "Users",
            "models": ["erp_crm_customers", "erp_crm_contacts"]
        }
    ]
