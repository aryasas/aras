"""maint_agents — Claude-powered maintenance agents.

DEV-MODE ONLY. Endpoints refuse unless ARAS_MODE=development AND user is admin.
"""
from arasCore.arasgen import ArasGen
from arasCore.lib.services.app_helper import CustomRoute

from app.maint_agents.services import handlers as h


class MaintAgents(ArasGen.App):
    name  = "maint_agents"
    title = "Maintenance Agents"
    icon  = "fa-wrench"
    order = 91
    custom_routes = [
        CustomRoute("/doc-sync",    h.handle_doc_sync,    methods=["POST"]),
        CustomRoute("/form-layout", h.handle_form_layout, methods=["POST"]),
    ]


helper = MaintAgents.helper
