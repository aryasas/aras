import os
from flask import Blueprint

_app_erp_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app_bp = Blueprint(
    "erp_views", __name__,
    url_prefix="/admin/erp",
    template_folder=os.path.join(_app_erp_dir, "templates"),
    static_folder=os.path.join(_app_erp_dir, "static"),
    static_url_path="/erp_static",
)

# Register models with SQLAlchemy before db.create_all()
import aras.app_erp.erp_core.models   # noqa
import aras.app_erp.erp_acc.models    # noqa
import aras.app_erp.erp_crm.models    # noqa
import aras.app_erp.erp_pos.models    # noqa
import aras.app_erp.erp_stock.models  # noqa

from . import core  # noqa
from . import pos   # noqa
