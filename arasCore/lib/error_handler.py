import logging
import traceback as _tb
from flask import render_template, current_app
from flask import json, request
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def json_response():
    return (
        request.accept_mimetypes["application/json"]
        >= request.accept_mimetypes["text/html"]
    )


def register_errorhandlers(app):
    def render_error(error):
        error_code = getattr(error, "code", 500)
        tmpl = f"page_{error_code}.html"
        try:
            return render_template(tmpl), error_code
        except Exception:
            return f"<h1>{error_code}</h1>", error_code

    for errcode in [401, 403, 404, 500]:
        app.errorhandler(errcode)(render_error)

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        if isinstance(e, HTTPException):
            return render_error(e)
        logger.error("Unhandled exception: %s\n%s", e, _tb.format_exc())
        if current_app.config.get("DEBUG"):
            raise e
        try:
            return render_template("page_500.html"), 500
        except Exception:
            return "<h1>500 Internal Server Error</h1>", 500

    return None


# @app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps(
        {
            "code": e.code,
            "name": e.name,
            "description": e.description,
        }
    )
    response.content_type = "application/json"
    return response


# @app.errorhandler(Exception)
# @app.route("/errortest")
def handle_exception(e):
    # pass through HTTP errors
    if isinstance(e, HTTPException):
        return e

    # now you're handling non-HTTP exceptions only
    return render_template("page_500.html", e=e), 500


"""
ACTIVATE THIS ERROR HANDLER IN PRODUCTION
"""
# @app.errorhandler(Exception)
# def unhandled_exception(e):
#     app.logger.error('Unhandled Exception: %s' % e)
#     return render_template('page_500.html',
#                            event_id=g.sentry_event_id,
#                            public_dsn=sentry.client.get_public_dsn('https')), 500


# @app.errorhandler(500)
# def internal_server_error(error):
#     app.logger.error('Server Error: %s' % error)
#     return render_template('page_500.html',
#                            event_id=g.sentry_event_id,
#                            public_dsn=sentry.client.get_public_dsn('https')), 500


# @app.errorhandler(404)
# def page_not_found(error):
#     app.logger.error('Page not found: %s' % request.path)
#     return render_template('page_404.html',
#                            event_id=g.sentry_event_id,
#                            public_dsn=sentry.client.get_public_dsn('https')), 404
