# -*- coding: utf-8 -*-
"""
arasCore/lib/script_runner.py
Safe server-side script execution sandbox.

Sandbox mode is controlled by a framework DB setting:
  key="script_sandbox_extended"  value_type="boolean"
  - False (default): only safe builtins, no stdlib
  - True: whitelisted modules available (datetime, math, re, json, decimal)

Scripts receive a `doc` context variable (the model instance as dict)
and a `frappe`-style `throw(msg)` helper to raise validation errors.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

_SAFE_BUILTINS = {
    "abs": abs, "round": round, "min": min, "max": max, "sum": sum,
    "len": len, "int": int, "float": float, "str": str, "bool": bool,
    "list": list, "dict": dict, "set": set, "tuple": tuple,
    "enumerate": enumerate, "zip": zip, "range": range, "sorted": sorted,
    "reversed": reversed, "any": any, "all": all, "print": print,
    "True": True, "False": False, "None": None,
    "isinstance": isinstance, "hasattr": hasattr, "getattr": getattr,
}

_EXTENDED_MODULES = {
    "datetime": __import__("datetime"),
    "math":     __import__("math"),
    "re":       __import__("re"),
    "json":     __import__("json"),
    "decimal":  __import__("decimal"),
}


def _is_extended_sandbox() -> bool:
    try:
        from arasCore.arasAdmin.models import ArasSystemSetting
        return ArasSystemSetting.get("script_sandbox_extended", False) is True
    except Exception:
        pass
    return False


def _build_globals(extended: bool) -> dict:
    g = {"__builtins__": _SAFE_BUILTINS}
    if extended:
        g.update(_EXTENDED_MODULES)
    return g


def _throw(message: str):
    raise ValueError(message)


def run_script(code: str, context: dict) -> Any:
    """
    Execute a script snippet in the configured sandbox.
    `context` keys are injected as local variables.
    `doc` is always the primary context dict.
    Raises ValueError on script-initiated throw().
    Returns the local namespace after execution.
    """
    if not code or not code.strip():
        return {}
    extended = _is_extended_sandbox()
    globs = _build_globals(extended)
    locs = dict(context)
    locs["throw"] = _throw
    try:
        exec(code, globs, locs)  # noqa: S102
    except ValueError:
        raise
    except Exception as e:
        logger.warning(f"[script_runner] execution error: {e}")
        raise ValueError(f"Script error: {e}")
    return locs


def run_scripts_for_event(app_slug: str, resource: str, event: str, obj) -> None:
    """
    Load and execute all active SrvScript rows matching (app, resource, event).
    Passes obj.to_dict() as `doc`. Raises ValueError to cancel on throw().
    """
    try:
        from arasCore.lib.script_models import SrvScript
        scripts = SrvScript.query.filter_by(
            app=app_slug, resource=resource, event=event, active=True
        ).all()
    except Exception:
        return
    if not scripts:
        return
    doc = obj.to_dict() if hasattr(obj, "to_dict") else {"id": getattr(obj, "id", None)}
    for script in scripts:
        run_script(script.code, {"doc": doc, "obj": obj})
