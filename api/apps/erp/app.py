from core import Aras

class ErpApp(Aras.App):
    app_name = "erp"
    app_label = "ERP System"
    icon = "Briefcase"
    have_home = True
    
    # Models are now managed by sub-apps:
    # erp_accounting, erp_stock, erp_crm, erp_supplier, erp_pos, erp_config
    models = []

    menu_groups = [
        {
            "label": "Modules",
            "icon": "LayoutGrid",
            "apps": ["erp_accounting", "erp_stock", "erp_crm", "erp_supplier", "erp_pos", "erp_config"]
        }
    ]
