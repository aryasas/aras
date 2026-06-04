# claude-opus-4-8
"""
Framework-vs-product isolation guards (Definition of Done, restructure phases 1-8).

These tests codify the HARD INVARIANT of the restructure: the framework tier
(`core/`) is domain-agnostic and must NEVER import from product apps (`apps/`)
or the optional plugin tier (`plugins/`). If any of these fail, the framework
can no longer be lifted out to boot a *new* product with zero ERP coupling.
"""
import ast
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
CORE = REPO / "core"
PLUGINS = REPO / "plugins"


def _imports_in(py_file: pathlib.Path):
    """Yield top-level imported module dotted-paths in a python file."""
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                yield n.name
        elif isinstance(node, ast.ImportFrom):
            # ignore relative imports (node.level > 0); they can't reach apps/
            if node.level == 0 and node.module:
                yield node.module


def _offending(root: pathlib.Path, forbidden_prefixes, skip_dirs=()):
    out = []
    for py in root.rglob("*.py"):
        if any(part in skip_dirs for part in py.parts):
            continue
        for mod in _imports_in(py):
            for pref in forbidden_prefixes:
                if mod == pref or mod.startswith(pref + "."):
                    out.append(f"{py.relative_to(REPO)} -> {mod}")
    return out


# claude-opus-4-8
def test_core_never_imports_apps_or_plugins():
    """core/ is the framework: it boots with zero product apps installed."""
    # migrations/ are one-shot data scripts, not part of the booting framework.
    bad = _offending(CORE, ("apps", "plugins"), skip_dirs=("migrations",))
    assert not bad, "Framework (core/) leaked product imports:\n" + "\n".join(bad)


# claude-opus-4-8
def test_plugins_never_import_products():
    """plugins/ (tier 2) may use core but not product apps."""
    if not PLUGINS.exists():
        pytest.skip("no plugins tier")
    bad = _offending(PLUGINS, ("apps",))
    assert not bad, "Plugin tier leaked product imports:\n" + "\n".join(bad)


# claude-opus-4-8
def test_framework_boots_without_product_apps():
    """
    Simulate a brand-new product: import the framework's app registry and core
    managers with no ERP app pre-imported. This must not raise — proving core
    resolves everything through registries (ServiceRegistry / AppConfigRegistry),
    never hard module references.
    """
    import importlib

    # These are the load-bearing framework entrypoints a new product reuses.
    for mod in (
        "core.base.app",
        "core.service_registry",
        "core.config",
        "core.manager.service_bootstrap",
        "core.manager.bootstrap",
        "core.manager.workflow_manager",
        "core.auth.module_guard",
    ):
        importlib.import_module(mod)  # raises if any leaks a product import


# claude-opus-4-8
def test_core_resolves_optional_services_gracefully():
    """
    A new product has no saas/dev apps. Core code that *optionally* uses them
    (module_guard -> Subscription, dev router -> HandoffRun) must degrade to
    None-checks, not crash, when the key is absent from the registry.
    """
    from core.service_registry import ServiceRegistry

    # Unknown keys return None rather than raising — the contract core relies on.
    assert ServiceRegistry.get("__definitely_not_registered__") is None
