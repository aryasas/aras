from core.base.app import App
from core.logic.discovery import autodiscover_models
from .models import *
from . import views
from .routers import router

class WebApp(App):
    app_name = "web"
    app_label = "Web / CMS"
    icon = "Globe"
    have_home = True
    routers = [router]
    models = autodiscover_models(__name__, ["models"])

    @classmethod
    def seed(cls, db):
        from .seed_landing import seed_landing_sections
        seed_landing_sections(db)
