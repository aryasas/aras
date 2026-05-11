"""dev_agents — Claude-powered build agents.

DEV-MODE ONLY. Endpoints refuse unless ARAS_MODE=development AND user is admin.
"""
from arasCore.arasgen import ArasGen
from arasCore.lib.services.app_helper import CustomRoute

from app.dev_agents.services import handlers as h


class DevAgents(ArasGen.App):
    name  = "dev_agents"
    title = "Dev Agents"
    icon  = "fa-robot"
    order = 90
    custom_routes = [
        CustomRoute("/uiux",     h.handle_uiux,     methods=["POST"]),
        CustomRoute("/coder",    h.handle_coder,    methods=["POST"]),
        CustomRoute("/reviewer", h.handle_reviewer, methods=["POST"]),
        CustomRoute("/pipeline", h.handle_pipeline, methods=["POST"]),
    ]


helper = DevAgents.helper
