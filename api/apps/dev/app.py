from core import Aras

class DevToolsApp(Aras.App):
    """
    Advanced Developer Tools for framework maintenance and inspection.
    """
    app_name = "dev"
    app_label = "Developer Tools"
    description = "Framework inspection, metadata management, and database tools."
    icon = "Terminal"
    
    # Core models are now strictly part of the framework registry.
    # DevTools simply provides a custom UI to inspect them.
    models = []
