"""
Generic function to submit an agent task report directly to the DB (dev_handoff_runs).

Usage (standalone):
    python tools/agent_report.py --feature "auth fix" --backend "arasCore/auth.py" \
        --features-added "JWT refresh" --input-tokens 3200 --output-tokens 800

Usage (from any script / multi_agent / Claude inline):
    from tools.agent_report import agent_report
    agent_report(
        feature="auth fix",
        backend_files="arasCore/auth.py",
        input_tokens=3200,
        output_tokens=800,
    )
"""

import argparse
import sys
from datetime import datetime, timezone
from typing import Optional

import requests

API_BASE = "http://localhost:8000/api/v1"


# claude-sonnet-4-6
def _get_token(api_base: str = API_BASE) -> str:
    res = requests.post(
        f"{api_base}/auth/token",
        data={"username": "admin", "password": "admin"},
        timeout=5,
    )
    if res.status_code != 200:
        raise RuntimeError(f"Login failed: {res.status_code} {res.text}")
    return res.json()["access_token"]


# claude-sonnet-4-6
def agent_report(
    feature: str,
    *,
    # mode / status
    mode: Optional[str] = None,                  # full | backend-only | frontend-only; auto-detected
    status: str = "success",                      # success | error | partial

    # run metadata
    run_date: Optional[str] = None,              # ISO datetime; defaults to now
    author: str = "Claude Code",                 # Claude Code | human | gemini | codex

    # files touched (flat strings, comma or newline separated)
    backend_files: Optional[str] = None,
    frontend_files: Optional[str] = None,

    # issues
    issues: Optional[str] = None,

    # review
    verdict: Optional[str] = "APPROVED",        # APPROVED | NEEDS-FIX
    review: Optional[str] = None,               # full review text
    revision_count: int = 0,

    # token counts — Claude
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,

    # token counts — Gemini
    gemini_prompt_tokens: int = 0,
    gemini_completion_tokens: int = 0,

    # token counts — GPT
    gpt_prompt_tokens: int = 0,
    gpt_completion_tokens: int = 0,

    # totals (auto-calculated from above if not set)
    total_tokens: int = 0,
    total_requests: int = 0,

    # git
    commit_hash: Optional[str] = None,
    commit_message: Optional[str] = None,

    # connection
    api_base: str = API_BASE,
) -> dict:
    """Submit one task report directly to dev_handoff_runs via the REST API."""
    if not feature:
        raise ValueError("feature is required")

    # auto-detect mode
    if mode is None:
        if backend_files and frontend_files:
            mode = "full"
        elif backend_files:
            mode = "backend-only"
        elif frontend_files:
            mode = "frontend-only"
        else:
            mode = "full"

    # total_tokens = all agent tokens combined
    if not total_tokens:
        total_tokens = (
            input_tokens + output_tokens + cache_read_tokens + cache_write_tokens
            + gemini_prompt_tokens + gemini_completion_tokens
            + gpt_prompt_tokens + gpt_completion_tokens
        )

    payload = {
        "feature": feature,
        "mode": mode,
        "status": status,
        "run_date": run_date or datetime.now(timezone.utc).isoformat(),
        "author": author,
        "backend_files": backend_files or None,
        "frontend_files": frontend_files or None,
        "issues": issues or None,
        "claude_verdict": verdict,
        "claude_review": review or None,
        "revision_count": revision_count,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_tokens": cache_read_tokens,
        "cache_write_tokens": cache_write_tokens,
        "gemini_prompt_tokens": gemini_prompt_tokens,
        "gemini_completion_tokens": gemini_completion_tokens,
        "gpt_prompt_tokens": gpt_prompt_tokens,
        "gpt_completion_tokens": gpt_completion_tokens,
        "total_tokens": total_tokens,
        "total_requests": total_requests,
        "commit_hash": commit_hash or None,
        "commit_message": commit_message or None,
    }

    token = _get_token(api_base)
    headers = {"Authorization": f"Bearer {token}"}

    res = requests.post(
        f"{api_base}/dev/dev_handoff_runs",
        json=payload,
        headers=headers,
        timeout=10,
    )
    if res.status_code not in (200, 201):
        raise RuntimeError(f"Failed to create report: {res.status_code} {res.text}")

    record = res.json()
    print(f"[agent_report] Report #{record.get('id')} saved — {feature}")
    return record


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Submit an agent report to the DB.")
    parser.add_argument("--feature", required=True)
    parser.add_argument("--mode", choices=["full", "backend-only", "frontend-only"])
    parser.add_argument("--status", default="success", choices=["success", "error", "partial"])
    parser.add_argument("--run-date")
    parser.add_argument("--author", default="Claude Code")
    parser.add_argument("--backend", dest="backend_files")
    parser.add_argument("--frontend", dest="frontend_files")
    parser.add_argument("--issues")
    parser.add_argument("--verdict", default="APPROVED")
    parser.add_argument("--review")
    parser.add_argument("--revision-count", type=int, default=0)
    parser.add_argument("--input-tokens", type=int, default=0)
    parser.add_argument("--output-tokens", type=int, default=0)
    parser.add_argument("--cache-read-tokens", type=int, default=0)
    parser.add_argument("--cache-write-tokens", type=int, default=0)
    parser.add_argument("--gemini-prompt-tokens", type=int, default=0)
    parser.add_argument("--gemini-completion-tokens", type=int, default=0)
    parser.add_argument("--gpt-prompt-tokens", type=int, default=0)
    parser.add_argument("--gpt-completion-tokens", type=int, default=0)
    parser.add_argument("--total-tokens", type=int, default=0)
    parser.add_argument("--total-requests", type=int, default=0)
    parser.add_argument("--commit-hash")
    parser.add_argument("--commit-message")
    parser.add_argument("--api-base", default=API_BASE)

    args = parser.parse_args()
    try:
        agent_report(
            feature=args.feature,
            mode=args.mode,
            status=args.status,
            run_date=args.run_date,
            author=args.author,
            backend_files=args.backend_files,
            frontend_files=args.frontend_files,
            issues=args.issues,
            verdict=args.verdict,
            review=args.review,
            revision_count=args.revision_count,
            input_tokens=args.input_tokens,
            output_tokens=args.output_tokens,
            cache_read_tokens=args.cache_read_tokens,
            cache_write_tokens=args.cache_write_tokens,
            gemini_prompt_tokens=args.gemini_prompt_tokens,
            gemini_completion_tokens=args.gemini_completion_tokens,
            gpt_prompt_tokens=args.gpt_prompt_tokens,
            gpt_completion_tokens=args.gpt_completion_tokens,
            total_tokens=args.total_tokens,
            total_requests=args.total_requests,
            commit_hash=args.commit_hash,
            commit_message=args.commit_message,
            api_base=args.api_base,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _cli()
