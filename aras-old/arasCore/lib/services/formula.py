# -*- coding: utf-8 -*-
"""
arasCore/lib/formula.py
Safe formula evaluator for computed fields.

Formula expressions are Python expressions stored in AppManagerColumn.formula.
They are evaluated server-side at serialize time with the row as context.

Example formulas:
    "qty * unit_price"
    "subtotal * (1 + tax_rate / 100)"
    "round(total - discount, 2)"
"""
import logging

logger = logging.getLogger(__name__)

_SAFE_BUILTINS = {
    "abs": abs, "round": round, "min": min, "max": max,
    "sum": sum, "len": len, "int": int, "float": float,
    "str": str, "bool": bool, "list": list, "dict": dict,
    "True": True, "False": False, "None": None,
}


def evaluate_formula(expr: str, context: dict) -> object:
    """
    Evaluate a formula expression against a row context dict.
    Returns computed value, or None on error.
    """
    if not expr or not expr.strip():
        return None
    try:
        return eval(  # noqa: S307
            expr,
            {"__builtins__": _SAFE_BUILTINS},
            {k: (v if v is not None else 0) for k, v in context.items()},
        )
    except Exception as e:
        logger.debug(f"[formula] eval error '{expr}': {e}")
        return None


def apply_formulas(row_dict: dict, table_columns) -> dict:
    """
    Given a row dict and the table's column definitions,
    compute and inject all formula field values.
    """
    result = dict(row_dict)
    for col in table_columns:
        formula = getattr(col, "formula", None)
        if formula and formula.strip():
            result[col.name] = evaluate_formula(formula, result)
    return result
