# -*- coding: utf-8 -*-
"""@action — unify HTTP + CLI exposure for service functions.

Decorate a function once, framework auto-registers:
  • HTTP route   POST /api/<app>/<module>/<resource>/<func>
  • CLI command  flask aras <app>.<module>.<resource>.<func> --arg=...

Service functions stay pure (no Flask imports). Decorator builds adapters.

Example:
    from arasCore.lib.core.action import action

    @action()
    def post(payment_id: int):
        payment = AccPayment.get_or_404(payment_id)
        ...
        return {"id": payment.id, "state": "posted"}
"""
import inspect
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)

_REGISTRY: list["ActionMeta"] = []


@dataclass
class ActionMeta:
    fn:           Callable
    app:          str = ""        # erp / soc / todo (derived from module path)
    module:       str = ""        # acc / pos / stock (derived)
    file:         str = ""        # payment / invoice (derived from filename)
    name:         str = ""        # function name
    path:         str = ""        # explicit override for HTTP path; else derived
    methods:      list = field(default_factory=lambda: ["POST"])
    cli_name:     str = ""        # explicit CLI name; else derived dotted
    cli_group:    str = ""        # CLI group (defaults to app)
    cli_only:     bool = False
    http_only:    bool = False
    require_auth: bool = True
    description:  str = ""

    @property
    def http_path(self) -> str:
        if self.path:
            return self.path
        return f"/{self.module}/{self.file}/{self.name}"

    @property
    def http_url_key(self) -> str:
        return f"{self.app}{self.http_path}"

    @property
    def cli_command(self) -> str:
        if self.cli_name:
            return self.cli_name
        return f"{self.module}.{self.file}.{self.name}"


def action(
    *,
    path:         str = "",
    methods:      list | None = None,
    cli_name:     str = "",
    cli_group:    str = "",
    cli_only:     bool = False,
    http_only:    bool = False,
    require_auth: bool = True,
):
    """Mark a function as an action exposed to HTTP and/or CLI.

    Path/CLI-name auto-derived from module path:
        app.erp.erp_acc.services.payment.post →
            HTTP  POST /api/erp/acc/payment/post
            CLI   flask aras erp acc.payment.post
    """
    def deco(fn: Callable) -> Callable:
        meta = ActionMeta(
            fn=fn,
            name=fn.__name__,
            path=path,
            methods=list(methods) if methods else ["POST"],
            cli_name=cli_name,
            cli_group=cli_group,
            cli_only=cli_only,
            http_only=http_only,
            require_auth=require_auth,
            description=(fn.__doc__ or "").strip().split("\n")[0],
        )
        _populate_origin(meta, fn)
        fn._aras_action = meta            # type: ignore[attr-defined]
        _REGISTRY.append(meta)
        return fn
    return deco


def _populate_origin(meta: ActionMeta, fn: Callable) -> None:
    """Derive app/module/file from fn's module path.

    Expected layout: app.<app>.<app>_<module>.services.<file>
    e.g. app.erp.erp_acc.services.payment → app=erp, module=acc, file=payment
    """
    mod = fn.__module__ or ""
    parts = mod.split(".")
    # Defaults
    file_name = parts[-1] if parts else ""
    meta.file = file_name

    if len(parts) >= 2 and parts[0] == "app":
        meta.app = parts[1]
    if len(parts) >= 3:
        sub = parts[2]
        # erp_acc → acc, app_erp → erp (for non-namespaced apps just keep as-is)
        prefix = f"{meta.app}_"
        if sub.startswith(prefix):
            meta.module = sub[len(prefix):]
        else:
            meta.module = sub if sub != meta.app else ""

    if not meta.cli_group:
        meta.cli_group = meta.app


def get_actions() -> list[ActionMeta]:
    """Return all registered actions (snapshot)."""
    return list(_REGISTRY)


def actions_for_app(app: str) -> list[ActionMeta]:
    return [a for a in _REGISTRY if a.app == app]


def actions_for_cli_group(group: str) -> list[ActionMeta]:
    return [a for a in _REGISTRY if a.cli_group == group and not a.http_only]


def find_action(app: str, module: str, file: str, name: str) -> ActionMeta | None:
    for a in _REGISTRY:
        if a.app == app and a.module == module and a.file == file and a.name == name:
            return a
    return None


# ── HTTP adapter ──────────────────────────────────────────────────────────────

def make_http_view(meta: ActionMeta):
    """Wrap pure service fn into a Flask view: parse args, call, jsonify."""
    sig = inspect.signature(meta.fn)
    params = list(sig.parameters.values())

    def view(**url_kwargs):
        from flask import request, jsonify
        from arasCore.lib.core.extensions import db

        kwargs = dict(url_kwargs)

        # Pull JSON body for POST/PUT, query string for GET
        if request.method in ("POST", "PUT", "PATCH"):
            body = request.get_json(silent=True) or {}
        else:
            body = request.args.to_dict(flat=True)

        for p in params:
            if p.name in kwargs:
                continue
            if p.name in body:
                kwargs[p.name] = _coerce(body[p.name], p.annotation)
            elif p.default is inspect.Parameter.empty:
                return jsonify({"ok": False, "error": f"{p.name} required"}), 400

        try:
            result = meta.fn(**kwargs)
            payload = _serialize_result(result)
            return jsonify({"ok": True, **payload})
        except ValueError as e:
            db.session.rollback()
            return jsonify({"ok": False, "error": str(e)}), 400
        except Exception as e:
            db.session.rollback()
            logger.exception(f"[action] {meta.app}.{meta.module}.{meta.file}.{meta.name} failed")
            return jsonify({"ok": False, "error": str(e)}), 500

    view.__name__ = f"action_{meta.app}_{meta.module}_{meta.file}_{meta.name}"
    return view


def _coerce(value: Any, annotation: Any) -> Any:
    if annotation is inspect.Parameter.empty or value is None:
        return value
    try:
        if annotation is int:
            return int(value)
        if annotation is float:
            return float(value)
        if annotation is bool:
            if isinstance(value, str):
                return value.lower() in ("1", "true", "yes", "y", "on")
            return bool(value)
        if annotation is str:
            return str(value)
    except (TypeError, ValueError):
        pass
    return value


# ── CLI adapter ───────────────────────────────────────────────────────────────

def make_cli_command(meta: ActionMeta):
    """Wrap pure service fn into a click command with auto-derived options."""
    import click
    sig = inspect.signature(meta.fn)

    def callback(**kwargs):
        import flask
        app = flask.current_app._get_current_object()
        with app.app_context():
            from arasCore.lib.core.extensions import db
            try:
                result = meta.fn(**kwargs)
                db.session.commit()
                if result is not None:
                    click.echo(click.style(f"✓ {result}", fg="green"))
                else:
                    click.echo(click.style(f"✓ {meta.cli_command}", fg="green"))
            except Exception as e:
                db.session.rollback()
                click.echo(click.style(f"✗ {e}", fg="red"))
                raise click.Abort()

    cmd = click.Command(
        name=meta.cli_command,
        callback=callback,
        help=meta.description or meta.fn.__doc__,
    )
    for p in sig.parameters.values():
        opt = _click_option(p)
        if opt:
            cmd.params.append(opt)
    return cmd


def _click_option(p: inspect.Parameter):
    import click
    name = p.name
    flag = f"--{name.replace('_', '-')}"
    required = p.default is inspect.Parameter.empty
    default = None if required else p.default
    type_ = _click_type(p.annotation)
    return click.Option([flag], required=required, default=default, type=type_, show_default=not required)


def _click_type(annotation):
    import click
    if annotation is int:    return click.INT
    if annotation is float:  return click.FLOAT
    if annotation is bool:   return click.BOOL
    if annotation is str:    return click.STRING
    return None


# ── Discovery hooks ───────────────────────────────────────────────────────────

def autoload_services(pkg_name: str) -> int:
    """Import every services/*.py module under pkg_name to fire @action decorators.

    Returns count of modules imported.
    """
    import pkgutil
    from importlib import import_module
    try:
        root = import_module(pkg_name)
    except ImportError:
        return 0
    if not hasattr(root, "__path__"):
        return 0

    count = 0
    for _f, modname, _p in pkgutil.walk_packages(root.__path__, prefix=f"{pkg_name}."):
        parts = modname.split(".")
        if "services" not in parts:
            continue
        leaf = parts[-1]
        if leaf.startswith("_"):
            continue
        try:
            import_module(modname)
            count += 1
        except Exception as e:
            logger.warning(f"[action autoload] {modname}: {e}")
    return count


def _serialize_result(result) -> dict:
    """Coerce service return value into a JSON-safe dict."""
    if result is None:
        return {}
    if isinstance(result, dict):
        return result
    if isinstance(result, (list, tuple)):
        return {"data": [_one(r) for r in result]}
    return {"data": _one(result)}


def _one(obj):
    if hasattr(obj, "to_dict"):
        try:
            return obj.to_dict()
        except Exception:
            pass
    if hasattr(obj, "id"):
        return {"id": obj.id, "name": getattr(obj, "name", None)}
    return obj
