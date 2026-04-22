#!/usr/bin/env python3
"""
smart_read.py - Advanced Token & Context Manager for AI Coding Assistants
Prevents redundant file reads, returns unified diffs, and tracks token efficiency.
"""

import sys
import os
import json
import difflib
import argparse

CACHE_DIR = ".ai_cache"
STATS_FILE = os.path.join(CACHE_DIR, "stats.json")

def init_env():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def load_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {
        "total_reads": 0, "cache_hits": 0, "first_reads": 0,
        "changed_files": 0, "tokens_saved": 0, "total_tokens": 0
    }

def save_stats(stats):
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=4)

def estimate_tokens(text):
    # Standard heuristic: ~4 characters per token
    return len(text) // 4

def get_cache_path(filepath):
    # Flatten the filepath to create a safe cache filename
    safe_name = filepath.replace("/", "_").replace("\\", "_")
    return os.path.join(CACHE_DIR, safe_name)

def read_file(filepath):
    if not os.path.isfile(filepath):
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)

    init_env()
    stats = load_stats()
    stats["total_reads"] += 1

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            current_content = f.read()
    except UnicodeDecodeError:
        print(f"Error: '{filepath}' appears to be a binary file. Skipping.")
        sys.exit(1)

    current_tokens = estimate_tokens(current_content)
    stats["total_tokens"] += current_tokens
    cache_path = get_cache_path(filepath)

    # 1. FIRST READ LOGIC
    if not os.path.exists(cache_path):
        stats["first_reads"] += 1
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(current_content)
        save_stats(stats)
        print(f"--- FIRST READ: {filepath} ({current_tokens} tokens) ---")
        print(current_content)
        return

    # 2. SUBSEQUENT READ LOGIC
    with open(cache_path, 'r', encoding='utf-8') as f:
        cached_content = f.read()

    if current_content == cached_content:
        stats["cache_hits"] += 1
        stats["tokens_saved"] += current_tokens
        save_stats(stats)
        print(f"⚠️ FILE ALREADY IN CONTEXT. NO CHANGES DETECTED IN '{filepath}'.")
        return

    # 3. DIFF LOGIC
    stats["changed_files"] += 1

    cached_lines = cached_content.splitlines(keepends=True)
    current_lines = current_content.splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        cached_lines, current_lines,
        fromfile=f"cached_{filepath}", tofile=filepath, n=3
    ))

    diff_text = "".join(diff)
    diff_tokens = estimate_tokens(diff_text)

    if diff_tokens < current_tokens:
        stats["tokens_saved"] += (current_tokens - diff_tokens)

    with open(cache_path, 'w', encoding='utf-8') as f:
        f.write(current_content)

    save_stats(stats)
    print(f"⚠️ FILE ALREADY IN CONTEXT. SHOWING ONLY NEW CHANGES FOR '{filepath}':")
    print(diff_text)

def print_stats():
    stats = load_stats()
    savings_pct = 0
    if stats["total_tokens"] > 0:
        savings_pct = (stats["tokens_saved"] * 100) / stats["total_tokens"]

    print("=== Smart Read Token Optimization Stats ===")
    print(f"Total file reads:    {stats['total_reads']}")
    print(f"Cache hits (Blocked):{stats['cache_hits']}")
    print(f"First reads:         {stats['first_reads']}")
    print(f"Changed files (Diff):{stats['changed_files']}")
    print("-" * 40)
    print(f"Total read tokens:   ~{stats['total_tokens']}")
    print(f"Tokens saved:        ~{stats['tokens_saved']}")
    print(f"Efficiency Savings:  {savings_pct:.2f}%")
    print("===========================================")

def main():
    parser = argparse.ArgumentParser(description="AI Token Manager & Smart Reader")
    parser.add_argument("target", help="Filepath to read, or 'stats' to view metrics")

    args = parser.parse_args()

    if args.target.lower() == "stats":
        print_stats()
    else:
        read_file(args.target)

if __name__ == "__main__":
    main()
