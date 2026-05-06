import os
from flask import Blueprint

_erp_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app_bp = Blueprint(
    "erp_views", __name__,
    url_prefix="/admin/erp",
    template_folder=os.path.join(_erp_dir, "templates"),
    static_folder=os.path.join(_erp_dir, "static"),
    static_url_path="/erp_static",
)

# Models are auto-loaded by arasCore._autoload_models() — no manual imports needed.
from . import core  # noqa
from . import pos   # noqa
