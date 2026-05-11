from core import Aras
from .models import ArasSetting

class SystemApp(Aras.App):
    app_name = "system"
    app_label = "System Management"
    description = "Core system settings and user management."
    icon = "Settings"
    
    models = [Aras.User, ArasSetting]
