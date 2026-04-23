import logging
import traceback as _tb
from flask import render_template, current_app, jsonify, request
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

# ── JSON error envelope ───────────────────────────────────────────────────────

def api_error(status: int, code: str, message: str, details: dict = None):
    """Standard JSON error response: {"error": {"code", "message", "details"}}."""
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), status


def _exception_to_api_error(ex: Exception):
    """Map common exception types to structured API error responses."""
    if isinstance(ex, ValueError):
        return api_error(400, "VALIDATION", str(ex))
    if isinstance(ex, PermissionError):
        return api_error(403, "FORBIDDEN", str(ex))
    if isinstance(ex, LookupError):
        return api_error(404, "NOT_FOUND", str(ex))
    if isinstance(ex, IntegrityError):
        return api_error(409, "CONFLICT", "A record with these values already exists.")
    msg = str(ex)
    if current_app.config.get("DEBUG"):
        details = {"traceback": _tb.format_exc()}
        return api_error(500, "INTERNAL_ERROR", msg, details)
    return api_error(500, "INTERNAL_ERROR", "An internal error occurred.")


# ── Flask error handlers ──────────────────────────────────────────────────────

def _wants_json() -> bool:
    return (
        request.accept_mimetypes["application/json"]
        >= request.accept_mimetypes["text/html"]
        or request.path.startswith("/api/")
    )


def register_errorhandlers(app):
    def render_error(error):
        error_code = getattr(error, "code", 500)
        if _wants_json():
            msg = getattr(error, "description", str(error))
            return api_error(error_code, "HTTP_ERROR", msg)
        try:
            return render_template("page_error.html", error_code=error_code), error_code
        except Exception:
            return f"<h1>{error_code}</h1>", error_code

    for errcode in [400, 401, 403, 404, 405, 409, 500]:
        app.errorhandler(errcode)(render_error)

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        if isinstance(e, HTTPException):
            return render_error(e)
        logger.error("Unhandled exception: %s\n%s", e, _tb.format_exc())
        if _wants_json():
            return _exception_to_api_error(e)
        if current_app.config.get("DEBUG"):
            raise e
        try:
            return render_template("page_error.html", error_code=500), 500
        except Exception:
            return "<h1>500 Internal Server Error</h1>", 500
