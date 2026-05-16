from core import Aras

class ERP(Aras.App):
    app_name = "erp"
    app_label = "ERP System"
    icon = "Briefcase"
    have_home = True

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Automatically set parent_name and app_type for all ERP sub-apps
        if cls.app_name != "erp":
            cls.parent_name = "erp"
            cls.app_type = "module"
    
    # Models are now managed by sub-apps:
    # erp_accounting, erp_stock, erp_crm, erp_supplier, erp_pos, erp_config
    models = []
