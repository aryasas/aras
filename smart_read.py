#!/usr/bin/env python3
"""
smart_read.py - Token-efficient file reader for Claude Code.
- First read: returns full content
- Unchanged file: returns skip notice (never exits with error)
- Changed file: returns unified diff only

Cache is namespaced per Claude account so two accounts never share state.

Usage:
  python3 smart_read.py <filepath>
  python3 smart_read.py stats
  python3 smart_read.py reset

Account setup (run once per terminal per account):
  export CLAUDE_ACCOUNT=work      # account 1
  export CLAUDE_ACCOUNT=personal  # account 2
"""

import sys
import os
import json
import difflib
import hashlib
import argparse
from pathlib import Path

# Keep in sync with claude_token_guard.py
CHARS_PER_TOKEN = 4
GUARD_BASE = Path.home() / ".claude_token_guard"

# ─────────────────────────────────────────────
# ACCOUNT NAMESPACING
# ─────────────────────────────────────────────

def get_account_id() -> str:
    """
    Returns a namespace string for the current Claude account.
    Detection order:
      1. CLAUDE_ACCOUNT env var  — set manually per terminal/account
      2. CLAUDE_CONFIG_DIR       — Claude Code sets this per profile
      3. 'default'               — fallback (single account)
    """
    if os.environ.get("CLAUDE_ACCOUNT"):
        return os.environ["CLAUDE_ACCOUNT"]
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR", "")
    if config_dir:
        return hashlib.md5(config_dir.encode()).hexdigest()[:8]
    return "default"

def get_dirs():
    """Return (cache_dir, stats_file) for the current account."""
    account  = get_account_id()
    base     = GUARD_BASE / "accounts" / account
    return base / "file_cache", base / "smart_read_stats.json"

def init_env():
    cache_dir, _ = get_dirs()
    cache_dir.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# STATS
# ─────────────────────────────────────────────

def load_stats() -> dict:
    _, stats_file = get_dirs()
    if stats_file.exists():
        try:
            return json.loads(stats_file.read_text())
        except Exception:
            pass
    return {
        "account": get_account_id(),
        "total_reads": 0, "cache_hits": 0, "first_reads": 0,
        "changed_files": 0, "tokens_saved": 0, "total_tokens": 0,
    }

def save_stats(stats: dict):
    _, stats_file = get_dirs()
    stats_file.write_text(json.dumps(stats, indent=2))

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)

def get_cache_path(abs_path: str) -> Path:
    # MD5 of resolved absolute path — same method as claude_token_guard.py
    cache_dir, _ = get_dirs()
    key = hashlib.md5(abs_path.encode()).hexdigest()
    return cache_dir / key

# ─────────────────────────────────────────────
# CORE
# ─────────────────────────────────────────────

def read_file(filepath: str):
    init_env()
    abs_path = str(Path(filepath).resolve())

    if not os.path.isfile(abs_path):
        print(f"[smart_read] File not found: {filepath}")
        return  # never sys.exit — Claude must continue

    try:
        current_content = Path(abs_path).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"[smart_read] Could not read {filepath}: {e}")
        return

    stats = load_stats()
    stats["total_reads"] += 1
    current_tokens = estimate_tokens(current_content)
    stats["total_tokens"] += current_tokens
    cache_path = get_cache_path(abs_path)

    # ── FIRST READ ────────────────────────────────────────────────────────────
    if not cache_path.exists():
        stats["first_reads"] += 1
        cache_path.write_text(current_content, encoding="utf-8")
        save_stats(stats)
        print(f"[smart_read:{stats['account']}] FIRST READ: {filepath} (~{current_tokens} tokens)")
        print(current_content)
        return

    cached_content = cache_path.read_text(encoding="utf-8", errors="replace")

    # ── NO CHANGE ─────────────────────────────────────────────────────────────
    if current_content == cached_content:
        stats["cache_hits"] += 1
        stats["tokens_saved"] += current_tokens
        save_stats(stats)
        print(
            f"[smart_read:{stats['account']}] SKIP: '{filepath}' unchanged. "
            f"~{current_tokens} tokens saved. Use existing context."
        )
        return

    # ── CHANGED — return diff only ────────────────────────────────────────────
    stats["changed_files"] += 1
    diff_lines = list(difflib.unified_diff(
        cached_content.splitlines(keepends=True),
        current_content.splitlines(keepends=True),
        fromfile=f"{filepath} (cached)",
        tofile=f"{filepath} (current)",
        n=3,
    ))
    diff_text   = "".join(diff_lines)
    diff_tokens = estimate_tokens(diff_text)
    saved       = max(0, current_tokens - diff_tokens)
    stats["tokens_saved"] += saved

    cache_path.write_text(current_content, encoding="utf-8")
    save_stats(stats)

    print(
        f"[smart_read:{stats['account']}] DIFF: '{filepath}' changed. "
        f"diff ~{diff_tokens} tokens vs full ~{current_tokens} tokens. Saved ~{saved}."
    )
    print(diff_text)

# ─────────────────────────────────────────────
# STATS / RESET
# ─────────────────────────────────────────────

def print_stats():
    stats = load_stats()
    total = stats["total_tokens"]
    saved = stats["tokens_saved"]
    pct   = (saved * 100 / total) if total > 0 else 0

    print(f"=== Smart Read Stats [account: {stats['account']}] ===")
    print(f"Total reads    : {stats['total_reads']}")
    print(f"First reads    : {stats['first_reads']}")
    print(f"Cache hits     : {stats['cache_hits']}  (unchanged, skipped)")
    print(f"Diffs returned : {stats['changed_files']}  (changed, diff only)")
    print(f"Total tokens   : ~{total:,}")
    print(f"Tokens saved   : ~{saved:,}")
    print(f"Savings        : {pct:.1f}%")
    print("=" * 45)
    print(f"Cache dir      : {get_dirs()[0]}")
    print(f"To reset all   : py ~/.claude/claude_token_guard.py reset")

def reset_cache():
    init_env()
    cache_dir, stats_file = get_dirs()
    count = 0
    for f in cache_dir.glob("*"):
        f.unlink()
        count += 1
    if stats_file.exists():
        stats_file.unlink()
    print(f"[smart_read:{get_account_id()}] Reset: {count} cache files + stats cleared.")

# ─────────────────────────────────────────────
# ENTRYPOINT
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Token-efficient file reader for Claude Code")
    parser.add_argument("target", help="Filepath | 'stats' | 'reset' | 'whoami'")
    args = parser.parse_args()

    if args.target.lower() == "stats":
        print_stats()
    elif args.target.lower() == "reset":
        reset_cache()
    elif args.target.lower() == "whoami":
        print(f"Current account namespace: {get_account_id()}")
        print(f"Cache dir: {get_dirs()[0]}")
    else:
        read_file(args.target)

if __name__ == "__main__":
    main()
