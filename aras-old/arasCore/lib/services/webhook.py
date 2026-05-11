# -*- coding: utf-8 -*-
"""
arasCore/lib/webhook.py
Outbound webhook dispatcher. Fires POST requests to registered endpoints
when framework events are emitted.

Auto-subscribes to all events at app startup via init_webhooks(app).
Apps can also call fire_webhook() directly.
"""
import hmac
import hashlib
import json
import logging
import threading
from datetime import datetime, timezone

import requests as _requests
from arasCore.lib.core.tasks import huey

logger = logging.getLogger(__name__)


def _sign(payload_bytes: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()  # type: ignore[attr-defined]


@huey.task()
def dispatch_webhook_task(url: str, event: str, payload: dict, secret: str | None):
    """Background task to dispatch a single webhook POST."""
    body = json.dumps(payload, default=str).encode()
    headers = {
        "Content-Type": "application/json",
        "X-Aras-Event": event,
        "X-Aras-Timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if secret:
        headers["X-Aras-Signature"] = f"sha256={_sign(body, secret)}"
    try:
        resp = _requests.post(url, data=body, headers=headers, timeout=10)
        logger.debug(f"[webhook] {event} → {url} → {resp.status_code}")
    except Exception as e:
        logger.warning(f"[webhook] delivery failed to {url}: {e}")


def fire_webhook(event: str, payload: dict):
    """
    Fire all active webhooks whose event pattern matches.
    Offloads each dispatch to the Huey background task queue.
    """
    try:
        from arasCore.lib.models.webhook_models import WebhookEndpoint
        endpoints = WebhookEndpoint.query.filter_by(active=True).all()
    except Exception:
        return
    for ep in endpoints:
        if ep.event != "*" and ep.event != event:
            continue
        dispatch_webhook_task(ep.url, event, payload, ep.secret)


def _global_event_handler(event_name: str, obj=None, **kwargs):
    """Subscribed to all events. Converts obj to dict and fires webhooks."""
    try:
        payload = {}
        if obj is not None:
            if hasattr(obj, "to_dict"):
                payload = obj.to_dict()
            else:
                payload = {"id": getattr(obj, "id", None)}
        payload.update(kwargs)
        fire_webhook(event_name, {"event": event_name, "data": payload})
    except Exception as e:
        logger.warning(f"[webhook] handler error for '{event_name}': {e}")


def init_webhooks(app):
    """Call once at app startup to subscribe the global dispatcher."""
    try:
        from arasCore.lib.core.events import signal as get_signal
        # blinker's ANY sentinel — subscribe to all named signals
        from blinker import ANY
        from arasCore.lib.core import events as _ev
        # We patch into the emit() function: wrap it to also call our handler
        _original_emit = _ev.emit

        def _patched_emit(name, obj=None, sender=None, **kwargs):
            _original_emit(name, obj=obj, sender=sender, **kwargs)
            _global_event_handler(name, obj=obj, **kwargs)

        _ev.emit = _patched_emit
        logger.info("[webhook] global dispatcher initialized")
    except Exception as e:
        logger.warning(f"[webhook] init failed: {e}")
