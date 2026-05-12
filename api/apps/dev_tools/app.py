from core import Aras

class DevToolsApp(Aras.App):
    """
    Advanced Developer Tools for framework maintenance and inspection.
    """
    app_name = "dev_tools"
    app_label = "Developer Tools"
    description = "Framework inspection, metadata management, and database tools."
    icon = "Terminal"
    
    # Models related to framework metadata and logs
    models = [
        Aras.AppModel, 
        Aras.ResourceModel, 
        Aras.FieldModel, 
        Aras.LinkModel,
        Aras.ActivityLog
    ]
