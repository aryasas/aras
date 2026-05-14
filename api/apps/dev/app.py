from core import Aras

class DevApp(Aras.App):
    """
    Advanced Developer Tools for framework maintenance and inspection.
    """
    app_name = "dev"
    app_label = "Developer Tools"
    description = "Framework inspection, metadata management, and database tools."
    icon = "Terminal"
    
    models = [
        Aras.AppModel, 
        Aras.ResourceModel, 
        Aras.FieldModel, 
        Aras.LinkModel,
        Aras.ActivityLog,
        Aras.User,
        Aras.ArasSetting,
        Aras.WidgetModel,
        Aras.DashboardLayoutModel
    ]
