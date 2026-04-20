# -*- coding: utf-8 -*-
"""
test/helpers.py — Result recording and pretty-print helpers.
"""
import sys
import time
from typing import List, Tuple

PASS = "\033[92m✔\033[0m"
FAIL = "\033[91m✘\033[0m"
SKIP = "\033[93m–\033[0m"
BOLD = "\033[1m"
RESET = "\033[0m"

_results: List[Tuple[str, bool, str]] = []  # (name, passed, detail)


def record(name: str, passed: bool, detail: str = ""):
    _results.append((name, passed, detail))
    icon = PASS if passed else FAIL
    print(f"  {icon}  {name}" + (f"  [{detail}]" if detail else ""))


def section(title: str):
    print(f"\n{BOLD}── {title} {'─' * max(0, 50 - len(title))}{RESET}")


def summary():
    total  = len(_results)
    passed = sum(1 for _, p, _ in _results if p)
    failed = total - passed
    print(f"\n{'═' * 54}")
    print(f"  {BOLD}Results:{RESET}  {passed}/{total} passed", end="")
    if failed:
        print(f"  {FAIL} {failed} failed", end="")
    print()
    if failed:
        print(f"\n  {BOLD}Failures:{RESET}")
        for name, p, detail in _results:
            if not p:
                print(f"    {FAIL}  {name}" + (f"  → {detail}" if detail else ""))
    print()
    return failed


def assert_ok(name: str, condition: bool, detail: str = ""):
    record(name, condition, detail)
    return condition


def reset():
    _results.clear()
