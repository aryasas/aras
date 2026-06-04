"""Shared app install ordering for CLI and admin tooling."""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from core.base.app import App

_TIER_ORDER = {
    "framework": 0,
    "platform": 1,
    "app": 2,
    "module": 3,
}


def _unique_apps(apps: Iterable[type[App]]) -> dict[str, type[App]]:
    result: dict[str, type[App]] = {}
    for app_cls in apps:
        app_name = getattr(app_cls, "app_name", "") or app_cls.__name__
        result[app_name] = app_cls
    return result


def _tier_rank(app_cls: type[App]) -> tuple[int, str]:
    return (_TIER_ORDER.get(getattr(app_cls, "app_type", "app"), _TIER_ORDER["app"]), getattr(app_cls, "app_name", app_cls.__name__))


def _find_cycle(nodes: dict[str, type[App]], deps: dict[str, set[str]]) -> list[str] | None:
    visiting: list[str] = []
    state: dict[str, int] = {}

    def walk(name: str) -> list[str] | None:
        state[name] = 1
        visiting.append(name)
        for dep in sorted(deps[name], key=lambda value: _tier_rank(nodes[value])):
            dep_state = state.get(dep, 0)
            if dep_state == 0:
                cycle = walk(dep)
                if cycle:
                    return cycle
            elif dep_state == 1:
                start = visiting.index(dep)
                return visiting[start:] + [dep]
        visiting.pop()
        state[name] = 2
        return None

    for name in sorted(nodes, key=lambda value: _tier_rank(nodes[value])):
        if state.get(name, 0) == 0:
            cycle = walk(name)
            if cycle:
                return cycle
    return None


def resolve_install_order(registry: dict[str, type[App]] | None = None) -> list[type[App]]:
    """Return apps ordered by tier and declared dependencies.

    The registry keys are ignored; `app_name` is the identity used for dependency
    resolution because `requires` refers to app names, not Python class names.
    """

    if registry is None and not App._registry:
        from core.logic.discovery import discover_apps

        discover_apps(package_path="apps")

    source = registry if registry is not None else App._registry
    nodes = _unique_apps(source.values())
    if not nodes:
        return []

    deps: dict[str, set[str]] = {}
    reverse: dict[str, set[str]] = defaultdict(set)
    indegree: dict[str, int] = {}

    for app_name, app_cls in nodes.items():
        required = set(getattr(app_cls, "requires", []) or [])
        missing = sorted(dep for dep in required if dep not in nodes)
        if missing:
            raise ValueError(f"App '{app_name}' requires missing app(s): {', '.join(missing)}")
        deps[app_name] = required
        indegree[app_name] = len(required)
        for dep in required:
            reverse[dep].add(app_name)

    cycle = _find_cycle(nodes, deps)
    if cycle:
        raise ValueError(f"Dependency cycle detected: {' -> '.join(cycle)}")

    ready = sorted(
        [name for name, degree in indegree.items() if degree == 0],
        key=lambda value: _tier_rank(nodes[value]),
    )
    ordered: list[type[App]] = []

    while ready:
        name = ready.pop(0)
        ordered.append(nodes[name])
        for dependent in sorted(reverse.get(name, ()), key=lambda value: _tier_rank(nodes[value])):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)
        ready.sort(key=lambda value: _tier_rank(nodes[value]))

    if len(ordered) != len(nodes):
        raise ValueError("Failed to resolve install order.")
    return ordered
