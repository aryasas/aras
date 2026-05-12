"""
Purpose: The main Application manifest for the Admin (Control Center) module.
Context: Level 3 Implementation. Inherits from Aras.App (Level 2).
Impact: Registers the Admin module and its models (Settings, Users) into the framework.
"""
from core import Aras
from .models import ArasSetting

class AdminApp(Aras.App):
    """
    Control Center application for managing the framework.
    """
    app_name = "admin"
    app_label = "Control Center"
    description = "Administrative tools, user management, and system settings."
    icon = "Shield"
    
    # Models owned by this application
    models = [Aras.User, ArasSetting]
