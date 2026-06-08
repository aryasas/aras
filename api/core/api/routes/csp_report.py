# gemini-3-flash-preview
import logging
from fastapi import APIRouter, Request, status

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Security"])


# claude-opus-4-8
# The body is parsed as raw json (browsers send report-uri and report-to in different shapes);
# we deliberately log only non-PII fields, so no response model is needed.
@router.post("/csp-report", status_code=status.HTTP_204_NO_CONTENT)
async def handle_csp_report(request: Request):
    """
    Accepts CSP violation reports from browsers.
    Logs warnings with blocked-uri and violated-directive ONLY to avoid PII leak.
    Supports both legacy report-uri (single object) and modern report-to (array).
    """
    # Size cap check (simple check on Content-Length)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 10240: # 10KB cap
        return

    try:
        body = await request.json()
        
        # Modern report-to sends an array of reports
        if isinstance(body, list):
            for entry in body:
                if entry.get("type") == "csp-violation":
                    details = entry.get("body", {})
                    blocked_uri = details.get("blockedURL", "unknown")
                    violated_directive = details.get("effectiveDirective", "unknown")
                    logger.warning(
                        f"CSP Violation (report-to): blocked-uri='{blocked_uri}', violated-directive='{violated_directive}'"
                    )
            return

        # Legacy report-uri sends {"csp-report": {...}}
        report_data = body.get("csp-report", {})
        if report_data:
            blocked_uri = report_data.get("blocked-uri", "unknown")
            violated_directive = report_data.get("violated-directive", "unknown")
            logger.warning(
                f"CSP Violation (report-uri): blocked-uri='{blocked_uri}', violated-directive='{violated_directive}'"
            )
    except Exception:
        # Silently ignore malformed reports to avoid noise/DoS
        pass

    return
