#!/usr/bin/env python3
# claude-sonnet-4-6
"""Warn about untagged def/class in changed Python files.

Aras open-source rule (CLAUDE.md): every function/class written by an AI must carry
an attribution tag comment on the line above (e.g. `# claude-sonnet-4-6`, `# gpt-5`,
`# gemini-pro`). Human-written code may use `# human` to silence the warning.

Usage:
  python tools/check_attribution.py                # check git-staged *.py files
  python tools/check_attribution.py path/a.py ...  # check the given files
  python tools/check_attribution.py --all          # check all api/apps/*/models.py

Exit code is 0 (warn-only, non-blocking) by default so it never blocks a commit;
pass --strict to exit 1 when any untagged def/class is found.
"""
import re
import subprocess
import sys

# Accepted markers: an AI model name, `human` (hand-written), or `unattributed`
# (pre-existing code whose author predates the tagging rule — honest placeholder,
# not a fabricated model claim).
TAG = re.compile(r"#\s*(claude|gpt|chatgpt|codex|gemini|opus|sonnet|haiku|human|unattributed)", re.I)
DEF = re.compile(r"^(\s*)(class|def|async def)\s+(\w+)")


# claude-sonnet-4-6
def untagged_in(path: str) -> list[tuple[int, str]]:
    """Return (lineno, name) for each def/class lacking an attribution tag above it."""
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    out: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        m = DEF.match(line)
        if not m:
            continue
        # Skip dunder/private nested helpers? No — the rule applies to all defs/classes.
        j = i - 1
        tagged = False
        while j >= 0:  # walk up past decorators/blank lines to the nearest comment
            stripped = lines[j].strip()
            if stripped.startswith("@") or stripped == "":
                j -= 1
                continue
            tagged = bool(TAG.search(lines[j]))
            break
        if not tagged:
            out.append((i + 1, m.group(3)))
    return out


# claude-sonnet-4-6
def staged_py_files() -> list[str]:
    try:
        res = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [f for f in res.stdout.split() if f.endswith(".py")]


# claude-sonnet-4-6
def main(argv: list[str]) -> int:
    strict = "--strict" in argv
    argv = [a for a in argv if a != "--strict"]

    if "--all" in argv:
        import glob
        files = sorted(glob.glob("api/apps/*/models.py"))
    elif argv:
        files = argv
    else:
        files = staged_py_files()

    if not files:
        return 0

    total = 0
    for f in files:
        hits = untagged_in(f)
        if not hits:
            continue
        total += len(hits)
        print(f"\033[33m{f}\033[0m: {len(hits)} untagged def/class")
        for lineno, name in hits:
            print(f"  L{lineno}: {name}")

    if total:
        print(
            f"\n\033[33m⚠ {total} untagged def/class.\033[0m Add an attribution tag above each "
            "(e.g. `# claude-sonnet-4-6`, `# gpt-5`, `# human`, or `# unattributed`)."
        )
        return 1 if strict else 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
