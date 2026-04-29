# -*- coding: utf-8 -*-
"""
arasCore/lib/events.py
=======================
Blinker-based pub/sub event bus for cross-app communication.

Framework emits on every CRUD operation. Apps subscribe in manifest.py.

Usage — subscribing in manifest.py:
    from arasCore.lib.core.events import on
    on("erp/journal.created", lambda obj: ...)

Usage — emitting (done automatically by api_handler + services):
    from arasCore.lib.core.events import emit
    emit("erp/journal.created", obj)

Signal naming convention:
    "<app>/<resource>.<action>"
    e.g. "erp/acc_journal.created", "soc/post.deleted"

Actions: created, updated, deleted, submitted
"""
import logging

logger = logging.getLogger(__name__)

try:
    from blinker import Namespace
    _signals = Namespace()
    _BLINKER_AVAILABLE = True
except ImportError:
    _BLINKER_AVAILABLE = False
    logger.warning("[events] blinker not installed — event bus disabled. Run: pip install blinker")

# Registry of (signal_name → list[handler]) for display/debug
_subscriptions: dict = {}


def signal(name: str):
    """Return (or create) a named blinker signal. Use for advanced send() control."""
    if not _BLINKER_AVAILABLE:
        return _NoopSignal(name)
    return _signals.signal(name)


def emit(name: str, obj=None, sender=None, **kwargs):
    """
    Emit event `name` with payload obj.
    Silently no-ops if blinker is unavailable or no subscribers.
    """
    if not _BLINKER_AVAILABLE:
        return
    try:
        sig = _signals.signal(name)
        sig.send(sender or _sentinel, obj=obj, **kwargs)
        logger.debug(f"[events] emitted: {name}")
    except Exception as e:
        logger.warning(f"[events] emit error ({name}): {e}")


def on(name: str, handler):
    """
    Subscribe handler to event name.
    handler signature: handler(obj=None, **kwargs)
    Returns the handler (decorator-safe).
    """
    if not _BLINKER_AVAILABLE:
        return handler
    sig = _signals.signal(name)
    sig.connect(_wrap(handler), weak=False)
    _subscriptions.setdefault(name, []).append(handler)
    logger.debug(f"[events] subscribed: {name} → {handler}")
    return handler


def off(name: str, handler):
    """Unsubscribe handler from event name."""
    if not _BLINKER_AVAILABLE:
        return
    sig = _signals.signal(name)
    sig.disconnect(_wrap(handler))
    subs = _subscriptions.get(name, [])
    if handler in subs:
        subs.remove(handler)


def emit_crud(app_slug: str, resource_slug: str, action: str, obj=None, **kwargs):
    """
    Convenience: emit "app/resource.action".
    Called by api_handler and services after every CRUD op.
    """
    name = f"{app_slug}/{resource_slug}.{action}"
    emit(name, obj=obj, **kwargs)


# ── Decorator ─────────────────────────────────────────────────────────────────

def listener(name: str):
    """Decorator — @listener("erp/journal.created") def handle(obj): ..."""
    def decorator(fn):
        on(name, fn)
        return fn
    return decorator


# ── Internals ─────────────────────────────────────────────────────────────────

_sentinel = object()
_wrapper_cache: dict = {}


def _wrap(handler):
    """Blinker passes (sender, **kwargs) — adapt to handler(obj=None, **kwargs)."""
    if handler in _wrapper_cache:
        return _wrapper_cache[handler]

    def wrapper(sender, **kwargs):
        try:
            handler(**kwargs)
        except Exception as e:
            logger.warning(f"[events] handler {handler} raised: {e}")

    _wrapper_cache[handler] = wrapper
    return wrapper


class _NoopSignal:
    """Fallback when blinker is not installed."""
    def __init__(self, name): self.name = name
    def send(self, *a, **kw): pass
    def connect(self, *a, **kw): pass
    def disconnect(self, *a, **kw): pass
