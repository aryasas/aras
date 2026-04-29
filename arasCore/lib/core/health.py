"""
arasCore/lib/core/health.py — Startup health check + /admin/_health endpoint.

At startup, walks all active AppManagerApp entries and attempts to build
each model/form so failures surface at boot, not at first request.
"""
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def run_startup_checks(flask_app) -> dict:
    """Walk all active dynamic apps and validate model/form buildability."""
    global _last_result
    results = {"ok": [], "errors": [], "checked_at": datetime.now(timezone.utc).isoformat()}
    with flask_app.app_context():
        try:
            from arasCore.admin.models import AppManagerApp, AppManagerTable
            from arasCore.admin.services import make_table_model, make_table_form
            active_apps = AppManagerApp.query.filter_by(is_active=True).all()
            for app_obj in active_apps:
                tables = AppManagerTable.query.filter_by(app_id=app_obj.id, is_active=True).all()
                for tbl in tables:
                    label = f"{app_obj.slug}/{tbl.name}"
                    try:
                        model_cls = make_table_model(tbl, app_obj.slug)
                        make_table_form(tbl, model_cls, app_obj.id)
                        results["ok"].append(label)
                    except Exception as ex:
                        logger.warning(f"[health] {label} FAILED: {ex}")
                        results["errors"].append({"resource": label, "error": str(ex)})
        except Exception as ex:
            logger.error(f"[health] startup check failed: {ex}")
            results["errors"].append({"resource": "__startup__", "error": str(ex)})
    _last_result = results
    return results


_last_result: dict = {}


def register_health_endpoint(flask_app):
    """Mount GET /admin/_health/ returning JSON health status."""
    from flask import Blueprint, jsonify
    from flask_login import login_required

    bp = Blueprint("aras_health", __name__)

    @bp.route("/admin/_health/")
    @login_required
    def health_check():
        global _last_result
        if not _last_result:
            _last_result = run_startup_checks(flask_app)
        status = 200 if not _last_result.get("errors") else 207
        return jsonify({
            "status": "ok" if status == 200 else "degraded",
            **_last_result,
        }), status

    flask_app.register_blueprint(bp)
