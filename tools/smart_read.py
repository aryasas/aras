#!/usr/bin/env python3
"""
smart_read.py - Token-efficient file reader for Claude Code.
- First read: returns full content
- Unchanged file: returns skip notice (never exits with error)
- Changed file: returns unified diff only

Usage:
  python3 smart_read.py <filepath>
  python3 smart_read.py stats
  python3 smart_read.py reset
"""

import sys
import os
import json
import difflib
import argparse
from pathlib import Path

# Store cache globally so it works regardless of cwd
CACHE_DIR = Path.home() / "../.ai_cache"
STATS_FILE = CACHE_DIR / "stats.json"

def init_env():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def load_stats() -> dict:
    if STATS_FILE.exists():
        try:
            return json.loads(STATS_FILE.read_text())
        except Exception:
            pass
    return {
        "total_reads": 0, "cache_hits": 0, "first_reads": 0,
        "changed_files": 0, "tokens_saved": 0, "total_tokens": 0
    }

def save_stats(stats: dict):
    STATS_FILE.write_text(json.dumps(stats, indent=2))

def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)

def get_cache_path(filepath: str) -> Path:
    safe = str(Path(filepath).resolve()).replace("/", "_").replace("\\", "_")
    return CACHE_DIR / safe

def read_file(filepath: str):
    init_env()

    # Resolve to absolute path so cache key is stable regardless of cwd
    abs_path = str(Path(filepath).resolve())

    if not os.path.isfile(abs_path):
        # Never sys.exit — just print and return so Claude continues
        print(f"[smart_read] File not found: {filepath}")
        return

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
        print(f"[smart_read] FIRST READ: {filepath} (~{current_tokens} tokens)")
        print(current_content)
        return

    cached_content = cache_path.read_text(encoding="utf-8", errors="replace")

    # ── NO CHANGE ─────────────────────────────────────────────────────────────
    if current_content == cached_content:
        stats["cache_hits"] += 1
        stats["tokens_saved"] += current_tokens
        save_stats(stats)
        print(
            f"[smart_read] SKIP: '{filepath}' is unchanged since last read. "
            f"~{current_tokens} tokens saved. Use your existing context."
        )
        return

    # ── CHANGED — return diff only ────────────────────────────────────────────
    stats["changed_files"] += 1

    diff = list(difflib.unified_diff(
        cached_content.splitlines(keepends=True),
        current_content.splitlines(keepends=True),
        fromfile=f"{filepath} (cached)",
        tofile=f"{filepath} (current)",
        n=3,
    ))
    diff_text = "".join(diff)
    diff_tokens = estimate_tokens(diff_text)
    saved = max(0, current_tokens - diff_tokens)
    stats["tokens_saved"] += saved

    # Update cache to current version
    cache_path.write_text(current_content, encoding="utf-8")
    save_stats(stats)

    print(
        f"[smart_read] DIFF: '{filepath}' changed. "
        f"Showing diff (~{diff_tokens} tokens) instead of full file (~{current_tokens} tokens). "
        f"Saved ~{saved} tokens."
    )
    print(diff_text)

def print_stats():
    stats = load_stats()
    total = stats["total_tokens"]
    saved = stats["tokens_saved"]
    pct = (saved * 100 / total) if total > 0 else 0

    print("=== Smart Read Stats ===")
    print(f"Total reads    : {stats['total_reads']}")
    print(f"First reads    : {stats['first_reads']}")
    print(f"Cache hits     : {stats['cache_hits']}  (unchanged, skipped)")
    print(f"Diffs returned : {stats['changed_files']}  (changed, diff only)")
    print(f"Total tokens   : ~{total:,}")
    print(f"Tokens saved   : ~{saved:,}")
    print(f"Savings        : {pct:.1f}%")
    print("========================")

def reset_cache():
    init_env()
    for f in CACHE_DIR.glob("*"):
        f.unlink()
    print("[smart_read] Cache cleared.")

def main():
    parser = argparse.ArgumentParser(description="Token-efficient file reader for Claude Code")
    parser.add_argument("target", help="Filepath to read, 'stats' to view metrics, 'reset' to clear cache")
    args = parser.parse_args()

    if args.target.lower() == "stats":
        print_stats()
    elif args.target.lower() == "reset":
        reset_cache()
    else:
        read_file(args.target)

if __name__ == "__main__":
    main()
