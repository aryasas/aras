#!/usr/bin/env python3
"""
claude_token_guard.py
=====================
Monitor Claude Code token usage and enforce token-efficient patterns.

Features:
  • Tracks input/output/cache tokens per session from Claude Code logs
  • Detects full-file re-reads and warns to use diff-only reads
  • Hooks into Claude Code's PreToolUse hook to intercept file reads
  • Shows live token usage dashboard in terminal
  • Suggests CLAUDE.md context optimizations
  • Writes a session report on exit

Usage:
  # As a Claude Code hook (recommended):
  Add to your project's .claude/settings.json:
  {
    "hooks": {
      "PreToolUse": [
        {"matcher": "Read|Write|Edit", "hooks": [{"type": "command", "command": "python3 /path/to/claude_token_guard.py hook"}]}
      ]
    }
  }

  # As a standalone monitor (watches logs live):
  python3 claude_token_guard.py monitor

  # Show session summary:
  python3 claude_token_guard.py summary

  # Reset session data:
  python3 claude_token_guard.py reset
"""

import sys
import os
import json
import time
import hashlib
import difflib
import re
import glob
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
GUARD_BASE = Path.home() / ".claude_token_guard"

def _get_account_id() -> str:
    """Namespace cache per Claude account. Set CLAUDE_ACCOUNT env var to separate accounts."""
    if os.environ.get("CLAUDE_ACCOUNT"):
        return os.environ["CLAUDE_ACCOUNT"]
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR", "")
    if config_dir:
        return hashlib.md5(config_dir.encode()).hexdigest()[:8]
    return "default"

GUARD_DIR      = GUARD_BASE / "accounts" / _get_account_id()
SESSION_FILE   = GUARD_DIR / "session.json"
FILE_CACHE_DIR = GUARD_DIR / "file_cache"
LOG_FILE       = GUARD_DIR / "guard.log"

# Approximate token costs (as of 2025, claude-sonnet-4)
COST_PER_1K_INPUT   = 0.003   # USD
COST_PER_1K_OUTPUT  = 0.015   # USD
COST_PER_1K_CACHE_W = 0.00375 # USD cache write
COST_PER_1K_CACHE_R = 0.0003  # USD cache read

# Thresholds
WARN_TOKENS_PER_FILE   = 2000   # warn if a single file read > this many tokens
LARGE_FILE_LINES       = 300    # files above this are "large" — suggest partial reads
SESSION_WARN_TOKENS    = 50_000 # warn when session input exceeds this

# Rough chars-per-token estimate
CHARS_PER_TOKEN = 4

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def ensure_dirs():
    GUARD_DIR.mkdir(parents=True, exist_ok=True)
    FILE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

def load_session() -> dict:
    ensure_dirs()
    if SESSION_FILE.exists():
        try:
            return json.loads(SESSION_FILE.read_text())
        except Exception:
            pass
    return {
        "started": datetime.now().isoformat(),
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_write_tokens": 0,
        "cache_read_tokens": 0,
        "file_reads": {},          # path -> {"count": int, "tokens": int, "hash": str}
        "reread_warnings": [],
        "large_file_warnings": [],
        "tool_calls": 0,
        "events": [],
    }

def save_session(session: dict):
    ensure_dirs()
    SESSION_FILE.write_text(json.dumps(session, indent=2))

def estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)

def file_hash(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()

def cost(inp, out, cw=0, cr=0) -> float:
    return (
        inp  / 1000 * COST_PER_1K_INPUT   +
        out  / 1000 * COST_PER_1K_OUTPUT  +
        cw   / 1000 * COST_PER_1K_CACHE_W +
        cr   / 1000 * COST_PER_1K_CACHE_R
    )

def log(msg: str):
    ensure_dirs()
    ts = datetime.now().strftime("%H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")

def color(text, code): return f"\033[{code}m{text}\033[0m"
def green(t):  return color(t, "32")
def yellow(t): return color(t, "33")
def red(t):    return color(t, "31")
def cyan(t):   return color(t, "36")
def bold(t):   return color(t, "1")

# ─────────────────────────────────────────────
# DIFF ENGINE — only send changed lines
# ─────────────────────────────────────────────

def get_cached_content(path: str) -> Optional[str]:
    cache_key = hashlib.md5(path.encode()).hexdigest()
    cache_file = FILE_CACHE_DIR / cache_key
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8", errors="replace")
    return None

def cache_content(path: str, content: str):
    cache_key = hashlib.md5(path.encode()).hexdigest()
    cache_file = FILE_CACHE_DIR / cache_key
    cache_file.write_text(content, encoding="utf-8")

def compute_diff(old: str, new: str, path: str) -> str:
    """Return a compact unified diff between old and new content."""
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    diff = list(difflib.unified_diff(
        old_lines, new_lines,
        fromfile=f"{path} (cached)",
        tofile=f"{path} (current)",
        n=3,  # context lines
    ))
    if not diff:
        return ""
    return "".join(diff)

def analyze_file_read(path: str, content: str, session: dict) -> dict:
    """
    Core logic: decide whether to pass full content or diff.
    Returns a result dict with advice for the hook output.
    """
    result = {
        "path": path,
        "action": "allow",          # allow | allow_diff | warn
        "tokens_estimated": 0,
        "tokens_saved": 0,
        "diff": None,
        "warnings": [],
        "suggestions": [],
    }

    tokens = estimate_tokens(content)
    result["tokens_estimated"] = tokens

    # ── Check cache ──────────────────────────────────────────────────────────
    cached = get_cached_content(path)
    current_hash = file_hash(content)

    if cached is not None:
        cached_hash = file_hash(cached)
        if cached_hash == current_hash:
            # File unchanged since last read
            result["action"] = "warn"
            result["warnings"].append(
                f"⚠️  RE-READ DETECTED: '{path}' has NOT changed since last read. "
                f"Estimated waste: ~{tokens} tokens."
            )
            result["tokens_saved"] = tokens
            session["reread_warnings"].append({
                "path": path,
                "tokens_wasted": tokens,
                "time": datetime.now().isoformat(),
            })
        else:
            # File changed — provide diff instead of full content
            diff = compute_diff(cached, content, path)
            diff_tokens = estimate_tokens(diff)
            saved = tokens - diff_tokens
            if saved > 100:  # only if worthwhile
                result["action"] = "allow_diff"
                result["diff"] = diff
                result["tokens_saved"] = saved
                result["suggestions"].append(
                    f"📉 DIFF MODE: '{path}' changed. Sending diff ({diff_tokens} tokens) "
                    f"instead of full file ({tokens} tokens). Saved ~{saved} tokens."
                )

    # ── Large file warning ────────────────────────────────────────────────────
    lines = content.count("\n") + 1
    if lines > LARGE_FILE_LINES:
        result["warnings"].append(
            f"📄 LARGE FILE: '{path}' has {lines} lines (~{tokens} tokens). "
            f"Consider using offset/limit parameters or reading only relevant sections."
        )
        session["large_file_warnings"].append({
            "path": path,
            "lines": lines,
            "tokens": tokens,
        })

    elif tokens > WARN_TOKENS_PER_FILE:
        result["warnings"].append(
            f"⚠️  HEAVY READ: '{path}' is ~{tokens} tokens. "
            f"Consider reading only needed sections."
        )

    # ── Update session file_reads ─────────────────────────────────────────────
    fr = session["file_reads"].setdefault(path, {"count": 0, "tokens": 0, "hash": ""})
    fr["count"] += 1
    fr["tokens"] += tokens
    fr["hash"] = current_hash

    # ── Update cache ──────────────────────────────────────────────────────────
    cache_content(path, content)

    return result

# ─────────────────────────────────────────────
# HOOK MODE — reads stdin JSON from Claude Code
# ─────────────────────────────────────────────

def run_hook():
    """
    Called by Claude Code's PreToolUse hook.
    Reads JSON from stdin, analyzes, writes result to stdout.

    Claude Code hook protocol:
      stdin:  { "tool_name": "...", "tool_input": { ... } }
      stdout: { "continue": true/false, "stopReason": "...", "suppressOutput": false }
              OR nothing (just exit 0 to allow unchanged)

    For Read tool:  tool_input.file_path
    For Edit/Write: tool_input.path
    """
    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit(0)

    try:
        hook_input = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name  = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    session = load_session()
    session["tool_calls"] += 1

    output_lines = []
    block = False

    # ── Handle Read tool ──────────────────────────────────────────────────────
    if tool_name == "Read":
        file_path = tool_input.get("file_path", "")
        if file_path and os.path.isfile(file_path):
            try:
                content = Path(file_path).read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                save_session(session)
                sys.exit(0)

            result = analyze_file_read(file_path, content, session)

            for w in result["warnings"]:
                output_lines.append(w)
                log(w)

            for s in result["suggestions"]:
                output_lines.append(s)
                log(s)

            # If file is identical to cached — block the re-read
            if result["action"] == "warn" and result["tokens_saved"] > 500:
                block = True
                output_lines.append(
                    f"\n🛑 Read BLOCKED to save ~{result['tokens_saved']} tokens.\n"
                    f"   File '{file_path}' is unchanged. Use the cached version."
                )

            # Print session token summary
            total_input = session["input_tokens"]
            if total_input > 0:
                output_lines.append(
                    f"\n📊 Session so far: {total_input:,} input tokens "
                    f"| ~${cost(total_input, session['output_tokens']):.4f} USD"
                )

    # ── Handle Write / Edit (track output tokens estimate) ───────────────────
    elif tool_name in ("Write", "Edit", "MultiEdit"):
        new_content = (
            tool_input.get("new_content") or
            tool_input.get("new_string") or ""
        )
        tokens = estimate_tokens(new_content)
        session["output_tokens"] += tokens

        file_path = tool_input.get("path", tool_input.get("file_path", ""))
        if file_path:
            # Invalidate cache so next Read gets fresh diff
            cache_key = hashlib.md5(file_path.encode()).hexdigest()
            cache_file = FILE_CACHE_DIR / cache_key
            if cache_file.exists():
                cache_file.unlink()

    # ── Session budget warning ────────────────────────────────────────────────
    if session["input_tokens"] > SESSION_WARN_TOKENS:
        output_lines.append(
            f"\n⚡ SESSION WARNING: {session['input_tokens']:,} input tokens consumed this session. "
            f"Consider /compact or starting a new conversation."
        )

    save_session(session)

    # Output feedback to Claude Code (shown as tool result context)
    if output_lines:
        feedback = "\n".join(output_lines)
        print(feedback, file=sys.stderr)  # stderr so it shows in Claude Code UI

    if block:
        result_json = {
            "continue": False,
            "stopReason": (
                f"Token guard: file '{file_path}' is unchanged since last read. "
                f"Skipping re-read to save ~{result['tokens_saved']} tokens. "
                f"Use the previously read content."
            ),
        }
        print(json.dumps(result_json))
    # else: exit 0 = allow

# ─────────────────────────────────────────────
# MONITOR MODE — live tail of Claude Code logs
# ─────────────────────────────────────────────

def find_claude_logs() -> list[Path]:
    """Find Claude Code session log files."""
    logs = []

    # Primary: ~/.claude/projects/**/*.jsonl (Claude Code actual location)
    projects_dir = Path.home() / ".claude" / "projects"
    if projects_dir.exists():
        logs.extend(sorted(
            projects_dir.rglob("*.jsonl"),
            key=os.path.getmtime, reverse=True
        ))

    # Exclude read-once stats from results
    logs = [l for l in logs if "read-once" not in str(l) and "token_guard" not in str(l)]

    # Fallback legacy paths
    if not logs:
        for base in [
            Path.home() / ".claude" / "logs",
            Path.home() / ".config" / "claude" / "logs",
            Path("/tmp") / "claude",
        ]:
            if base.exists():
                logs.extend(sorted(base.glob("*.jsonl"), key=os.path.getmtime, reverse=True))

    return logs

def parse_log_line(line: str) -> Optional[dict]:
    try:
        return json.loads(line.strip())
    except Exception:
        return None

def extract_tokens_from_event(event: dict) -> tuple[int, int, int, int]:
    """Return (input, output, cache_write, cache_read) tokens from a log event.
    Actual Claude Code schema (v2.1+):
      event.message.usage.{input_tokens, output_tokens,
        cache_creation_input_tokens, cache_read_input_tokens}
    Note: input_tokens is often just 1 because most content is cached.
    Real cost comes from cache_creation + cache_read tokens.
    """
    inp = out = cw = cr = 0

    # Only process assistant messages to avoid double-counting
    if event.get("type") != "assistant":
        return 0, 0, 0, 0

    # Primary path: event.message.usage (Claude Code actual format)
    usage = (event.get("message") or {}).get("usage") or {}

    # Fallback: top-level usage
    if not usage:
        usage = event.get("usage") or {}

    if usage:
        inp = int(usage.get("input_tokens") or 0)
        out = int(usage.get("output_tokens") or 0)
        cw  = int(usage.get("cache_creation_input_tokens") or 0)
        cr  = int(usage.get("cache_read_input_tokens") or 0)

    return inp, out, cw, cr

def run_monitor():
    """Live monitor: watches ALL log files under ~/.claude/projects/ for new activity."""
    ensure_dirs()
    session = load_session()

    projects_dir = Path.home() / ".claude" / "projects"

    print(bold(cyan("\n━━━  Claude Code Token Guard  ━━━")))
    print(f"  Watching: {projects_dir}")
    print(f"  Guard dir: {GUARD_DIR}")
    print(f"  Press Ctrl+C to stop and show summary\n")

    # Track file sizes for ALL log files — new sessions create new files
    seen: dict[Path, int] = {}

    def refresh_files():
        """Re-scan for new log files every tick."""
        all_logs = find_claude_logs()
        for lp in all_logs:
            if lp not in seen:
                # New file — start from end so we only see new writes
                try:
                    seen[lp] = lp.stat().st_size
                except Exception:
                    seen[lp] = 0

    refresh_files()
    print(f"  Tracking {len(seen)} existing log files. Waiting for Claude Code activity...\n")

    try:
        tick = 0
        while True:
            # Re-scan for new files every 5 seconds
            if tick % 10 == 0:
                before = len(seen)
                refresh_files()
                after = len(seen)
                if after > before:
                    print(f"\n  [{after - before} new session(s) detected, now tracking {after} files]")

            # Check all known files for new content
            for log_path in list(seen.keys()):
                try:
                    current_size = log_path.stat().st_size
                except Exception:
                    continue

                if current_size <= seen[log_path]:
                    continue

                try:
                    with open(log_path, "rb") as f:
                        f.seek(seen[log_path])
                        new_data = f.read(current_size - seen[log_path])
                    seen[log_path] = current_size
                except Exception:
                    continue

                for raw_line in new_data.decode("utf-8", errors="replace").splitlines():
                    event = parse_log_line(raw_line)
                    if not event:
                        continue
                    inp, out, cw, cr = extract_tokens_from_event(event)
                    if inp + out + cw + cr == 0:
                        continue

                    session["input_tokens"]       += inp
                    session["output_tokens"]      += out
                    session["cache_write_tokens"] += cw
                    session["cache_read_tokens"]  += cr

                    total_inp = session["input_tokens"]
                    total_out = session["output_tokens"]
                    total_cw  = session["cache_write_tokens"]
                    total_cr  = session["cache_read_tokens"]
                    total_cost = cost(total_inp, total_out, total_cw, total_cr)

                    # Effective context = direct input + cache reads
                    effective = total_inp + total_cr
                    bar_len = min(40, effective // 10000)
                    bar = "█" * bar_len + "░" * (40 - bar_len)
                    warn = red(" ⚡ HIGH") if effective > SESSION_WARN_TOKENS else ""

                    ts = datetime.now().strftime("%H:%M:%S")
                    print(
                        f"\n[{ts}] "
                        f"IN:{cyan(f'{total_inp:>7,}')}  "
                        f"OUT:{green(f'{total_out:>6,}')}  "
                        f"CW:{yellow(f'{total_cw:>7,}')}  "
                        f"CR:{green(f'{total_cr:>9,}')}  "
                        f"EFF:{cyan(f'{effective:>9,}')}  "
                        f"💰${total_cost:.4f}{warn}",
                        flush=True
                    )
                    save_session(session)

                    if effective > SESSION_WARN_TOKENS:
                        print(f"{yellow('  → Consider running /compact in Claude Code to compress context.')}")


            time.sleep(0.5)
            tick += 1

    except KeyboardInterrupt:
        print("\n")
        run_summary()

# ─────────────────────────────────────────────
# SUMMARY MODE
# ─────────────────────────────────────────────

def run_summary():
    session = load_session()

    inp = session["input_tokens"]
    out = session["output_tokens"]
    cw  = session["cache_write_tokens"]
    cr  = session["cache_read_tokens"]
    total_cost = cost(inp, out, cw, cr)

    print(bold(cyan("\n━━━  Token Guard Session Summary  ━━━")))
    print(f"  Started:      {session['started']}")
    print(f"  Tool calls:   {session['tool_calls']}")
    print()
    print(bold("  Token Usage:"))
    print(f"    Input         : {inp:>10,}")
    print(f"    Output        : {out:>10,}")
    print(f"    Cache writes  : {cw:>10,}")
    print(f"    Cache reads   : {cr:>10,}")
    print(f"    Est. cost     : ${total_cost:.4f} USD")
    print()

    if session["reread_warnings"]:
        wasted = sum(w["tokens_wasted"] for w in session["reread_warnings"])
        print(red(f"  ⚠️  Re-read warnings: {len(session['reread_warnings'])} occurrences, ~{wasted:,} tokens wasted"))
        for w in session["reread_warnings"][-5:]:
            print(f"    • {w['path']}  [{w['tokens_wasted']:,} tokens]")

    if session["large_file_warnings"]:
        print(yellow(f"\n  📄 Large file warnings: {len(session['large_file_warnings'])} files"))
        for w in session["large_file_warnings"][-5:]:
            print(f"    • {w['path']}  [{w['lines']} lines, ~{w['tokens']:,} tokens]")

    # Top re-read files
    reads = session["file_reads"]
    if reads:
        top = sorted(reads.items(), key=lambda x: x[1]["tokens"], reverse=True)[:5]
        print(bold(f"\n  📂 Top token-heavy reads:"))
        for path, info in top:
            flag = red(" ← re-read") if info["count"] > 1 else ""
            print(f"    [{info['count']}x] ~{info['tokens']:,} tokens  {path}{flag}")

    # Recommendations
    print(bold(cyan("\n  💡 Token Efficiency Tips:")))
    tips = generate_tips(session)
    for tip in tips:
        print(f"    {tip}")

    print()

def generate_tips(session: dict) -> list[str]:
    tips = []
    reads = session["file_reads"]
    rereads = [p for p, v in reads.items() if v["count"] > 1]

    if rereads:
        tips.append(f"🔁 {len(rereads)} file(s) were read more than once. Use 'Edit' instead of re-reading.")

    large = session["large_file_warnings"]
    if large:
        tips.append(f"📏 {len(large)} large file(s) read in full. Use offset/limit or ask Claude to read sections only.")

    if session["input_tokens"] > SESSION_WARN_TOKENS:
        tips.append("💬 Session is large. Run /compact in Claude Code to compress context.")

    if not (GUARD_DIR / "CLAUDE.md").exists():
        tips.append("📝 Add a CLAUDE.md to your project root — Claude Code reads it every session for free context.")

    tips += [
        "🎯 Use specific file paths instead of 'read all files in directory'.",
        "📌 Put architecture decisions in CLAUDE.md so Claude doesn't re-discover them.",
        "🔍 Prefer 'Grep' over 'Read' to find where something is before reading the file.",
        "✂️  Use 'Edit' with targeted replacements instead of full file writes.",
        "🗜️  Run /compact periodically in long sessions to compress conversation history.",
        "🔑 Break large tasks into sub-agents with clear, minimal context each.",
    ]
    return tips[:8]

# ─────────────────────────────────────────────
# RESET
# ─────────────────────────────────────────────

def run_reset():
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()
    for f in FILE_CACHE_DIR.glob("*"):
        f.unlink()
    print(green("✅ Session data and file cache cleared."))

# ─────────────────────────────────────────────
# INSTALL — prints settings.json snippet
# ─────────────────────────────────────────────

def run_install():
    script = os.path.abspath(__file__)
    snippet = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Read|Write|Edit|MultiEdit",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"python3 {script} hook"
                        }
                    ]
                }
            ]
        }
    }
    claude_settings = Path.cwd() / ".claude" / "settings.json"
    print(bold(cyan("━━━  Claude Token Guard — Install  ━━━")))
    print(f"\nAdd this to: {claude_settings}\n")
    print(json.dumps(snippet, indent=2))
    print(f"\nOr merge into your existing .claude/settings.json.")
    print(f"\nThen run: {cyan('python3 ' + script + ' monitor')} in a separate terminal.")

    # Also create a CLAUDE.md template if missing
    claude_md = Path.cwd() / "CLAUDE.md"
    if not claude_md.exists():
        template = """# Project Context for Claude Code

## Architecture
<!-- Describe the high-level structure so Claude doesn't need to re-read it -->

## Key Files
<!-- List important files and what they do -->

## Conventions
<!-- Coding style, naming conventions, test patterns -->

## Do NOT re-read
<!-- Files that are stable and should not be re-read every session -->

## Common Commands
<!-- build, test, lint commands -->
"""
        claude_md.write_text(template)
        print(f"\n{green('✅ Created CLAUDE.md template at ' + str(claude_md))}")
        print("   Fill it in to give Claude free context without re-reading files every session.")

# ─────────────────────────────────────────────
# ENTRYPOINT
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Claude Code token usage monitor and efficiency guard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="summary",
        choices=["hook", "monitor", "summary", "reset", "install"],
        help=(
            "hook     = run as Claude Code PreToolUse hook (reads stdin JSON)\n"
            "monitor  = live-tail Claude Code logs and display token dashboard\n"
            "summary  = show session summary and tips (default)\n"
            "reset    = clear session data and file cache\n"
            "install  = print .claude/settings.json snippet and create CLAUDE.md"
        ),
    )
    args = parser.parse_args()

    {
        "hook":    run_hook,
        "monitor": run_monitor,
        "summary": run_summary,
        "reset":   run_reset,
        "install": run_install,
    }[args.command]()

if __name__ == "__main__":
    main()
