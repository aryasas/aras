"""
ggc — Git commit + sync to reports.json and DB HandoffRun.

Usage:
    python tools/ggc.py "feat: my commit message"
    python tools/ggc.py "fix: something" --id 42      # attach to specific report entry
    python tools/ggc.py "fix: something" --tokens 5000

What it does:
    1. git add -A
    2. git commit -m "<message>"
    3. Gets commit hash (git rev-parse HEAD)
    4. Finds the latest report entry without a commit_hash (or --id entry)
    5. Updates that entry in reports.json and DB with commit_hash + commit_message + tokens
"""
import argparse
import json
import subprocess
import sys
import requests
from pathlib import Path
from typing import Optional

REPORTS_PATH = Path("docs/reports.json")
API_BASE = "http://localhost:8000/api/v1"


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip()


def _get_token() -> Optional[str]:
    try:
        res = requests.post(
            f"{API_BASE}/auth/token",
            data={"username": "admin", "password": "admin"},
            timeout=5,
        )
        if res.status_code == 200:
            return res.json()["access_token"]
    except Exception:
        pass
    return None


def _patch_db(db_id: int, patch: dict, headers: dict):
    try:
        res = requests.patch(
            f"{API_BASE}/dev/dev_handoff_runs/{db_id}",
            json=patch,
            headers=headers,
            timeout=5,
        )
        if res.status_code in (200, 201):
            print(f"  + DB updated  (id={db_id})")
        else:
            print(f"  x DB patch failed: {res.status_code} {res.text[:100]}")
    except Exception as e:
        print(f"  x DB unreachable: {e}")


def _find_db_id_by_feature(feature: str, headers: dict) -> Optional[int]:
    try:
        res = requests.get(
            f"{API_BASE}/dev/dev_handoff_runs",
            params={"page": 1, "page_size": 200},
            headers=headers,
            timeout=5,
        )
        if res.status_code == 200:
            items = res.json().get("items") or res.json().get("data", [])
            for item in items:
                if item.get("feature") == feature:
                    return item.get("id")
    except Exception:
        pass
    return None


def main():
    parser = argparse.ArgumentParser(description="Git commit + report sync")
    parser.add_argument("message", help="Commit message")
    parser.add_argument("--id", type=int, default=None, help="Report entry id to attach commit to")
    parser.add_argument("--tokens", type=int, default=0, help="Token count for this run")
    args = parser.parse_args()

    # 1. Stage all changes
    run(["git", "add", "-A"])

    # 2. Commit
    run(["git", "commit", "-m", args.message])
    commit_hash = run(["git", "rev-parse", "--short", "HEAD"])
    print(f"  Committed {commit_hash}: {args.message}")

    # 3. Load reports.json
    if not REPORTS_PATH.exists():
        print("  x docs/reports.json not found, skipping report update")
        return

    entries = json.loads(REPORTS_PATH.read_text())

    # 4. Find target entry
    if args.id:
        target = next((e for e in entries if e.get("id") == args.id), None)
        if not target:
            print(f"  x Entry id={args.id} not found in reports.json")
            return
    else:
        # Latest entry without a commit_hash
        uncommitted = [e for e in entries if not e.get("commit_hash")]
        if not uncommitted:
            print("  ! All entries already have a commit_hash. Use --id to attach to a specific entry.")
            return
        target = uncommitted[-1]

    # 5. Update JSON entry
    target["commit_hash"] = commit_hash
    target["commit_message"] = args.message
    if args.tokens:
        target["tokens"] = args.tokens

    REPORTS_PATH.write_text(json.dumps(entries, indent=2))
    print(f"  + JSON updated (id={target.get('id')}, feature={target.get('feature', '')[:50]})")

    # 6. Update DB
    auth_token = _get_token()
    if not auth_token:
        print("  ! API offline — DB not updated. Run sync_reports.py when API is up.")
        return

    headers = {"Authorization": f"Bearer {auth_token}"}
    db_id = _find_db_id_by_feature(target["feature"], headers)
    if db_id:
        patch = {"commit_hash": commit_hash, "commit_message": args.message}
        if args.tokens:
            patch["total_tokens"] = args.tokens
        _patch_db(db_id, patch, headers)
    else:
        print(f"  ! Feature not found in DB — run sync_reports.py to create it first.")


if __name__ == "__main__":
    main()
