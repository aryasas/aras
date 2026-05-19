from core.base.app import App
from core.logic.discovery import autodiscover_models
from .models import *
from . import views
from .routers import router

class SaaSApp(App):
    app_name = "saas"
    app_label = "SaaS Control Plane"
    icon = "Cloud"
    have_home = True
    routers = [router]
    models = autodiscover_models(__name__, ["models"])
