"""
Assert that stock services do not import accounting at module level.
This prevents the stock↔accounting circular import cycle from regressing.
In-function imports (indented inside a def) are permitted.
"""
import ast
import pathlib

STOCK_SERVICES = [
    "apps/stock/services/coa_resolver.py",
    "apps/stock/services/valuation.py",
    "apps/stock/services/workflow.py",
]

BASE = pathlib.Path(__file__).parent.parent


def _module_level_accounting_imports(filepath: str) -> list[str]:
    """Return any module-level 'from apps.accounting...' import lines."""
    src = (BASE / filepath).read_text()
    tree = ast.parse(src)
    violations = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("apps.accounting"):
                violations.append(f"line {node.lineno}: from {node.module} import ...")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("apps.accounting"):
                        violations.append(f"line {node.lineno}: import {alias.name}")
    return violations


def test_no_module_level_accounting_imports_in_stock_services():
    all_violations = {}
    for path in STOCK_SERVICES:
        violations = _module_level_accounting_imports(path)
        if violations:
            all_violations[path] = violations

    assert not all_violations, (
        "Module-level apps.accounting imports found in stock services (breaks import cycle):\n"
        + "\n".join(
            f"  {f}: {'; '.join(v)}"
            for f, v in all_violations.items()
        )
    )
