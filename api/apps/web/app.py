from core.base.app import App
from core.logic.discovery import autodiscover_models
from .models import *
from . import views
from .routers import router

class WebApp(App):
    app_name = "web"
    app_label = "Web / CMS"
    icon = "Globe"
    # saas_module gates the *admin authoring* CRUD (create/edit pages, menus,
    # sections). Public read of landing content stays open because the public
    # models are marked __public__ — RouterFactory skips the plan guard for those.
    saas_module = "web"
    have_home = True
    routers = [router]
    models = autodiscover_models(__name__, ["models"])

    @classmethod
    def seed(cls, db):
        from .seed_landing import seed_landing_sections
        seed_landing_sections(db)
