"""
Bidirectional sync between docs/reports.json and dev_handoff_runs DB table.
- JSON → DB: entries in JSON not in DB get created
- DB → JSON: entries in DB not in JSON get appended
- Match key: feature (unique per run)
- Run: python tools/sync_reports.py
"""
import json
import sys
import requests
from pathlib import Path

REPORTS_PATH = Path("docs/reports.json")
API_BASE = "http://localhost:8000/api/v1"

# Unified JSON schema — maps to DB columns
# reports.json entry:
# {
#   "id": int,             → DB id (set after create)
#   "date": "YYYY-MM-DD",  → run_date (date part only)
#   "feature": str,        → feature
#   "mode": str,           → mode (full | backend-only | frontend-only)
#   "status": str,         → status (success | error | partial)
#   "revision_count": int, → revision_count
#   "verdict": str,        → claude_verdict (APPROVED | NEEDS-FIX)
#   "tokens": int,         → total_tokens
#   "backend": {           → backend_files + output fragments
#     "files_written": str,
#     "features_added": str,
#     "fixes_applied": str,
#     "framework_changes": str,
#     "issues": str
#   } or null,
#   "frontend": same or null,
#   "notes": str           → notes
# }


def _get_token() -> str:
    try:
        res = requests.post(
            f"{API_BASE}/auth/token",
            data={"username": "admin", "password": "admin"},
            timeout=5,
        )
        if res.status_code != 200:
            print(f"Login failed: {res.status_code}")
            sys.exit(1)
        return res.json()["access_token"]
    except Exception as e:
        print(f"Cannot reach API: {e}")
        sys.exit(1)


def _fetch_all_db(headers: dict) -> list[dict]:
    runs = []
    page = 1
    while True:
        res = requests.get(
            f"{API_BASE}/dev/dev_handoff_runs",
            params={"page": page, "page_size": 100},
            headers=headers,
            timeout=10,
        )
        if res.status_code != 200:
            print(f"Failed to fetch DB runs: {res.status_code}")
            break
        data = res.json()
        items = data.get("items") or data.get("data", [])
        runs.extend(items)
        if len(items) < 100:
            break
        page += 1
    return runs


def _db_to_json(db: dict) -> dict:
    """Convert a DB HandoffRun record to reports.json schema."""
    date = (db.get("run_date") or "")[:10] or None

    # Try to parse backend/frontend from backend_files / frontend_files
    backend_files = db.get("backend_files") or ""
    frontend_files = db.get("frontend_files") or ""

    backend = None
    if backend_files and backend_files != "none":
        backend = {
            "files_written": backend_files,
            "features_added": "none",
            "fixes_applied": "none",
            "framework_changes": "none",
            "issues": db.get("issues") or "none",
        }

    frontend = None
    if frontend_files and frontend_files != "none":
        frontend = {
            "files_written": frontend_files,
            "features_added": "none",
            "fixes_applied": "none",
            "framework_changes": "none",
            "issues": "none",
        }

    return {
        "id": db.get("id"),
        "date": date,
        "feature": db.get("feature", ""),
        "mode": db.get("mode", "full"),
        "status": db.get("status", "success"),
        "revision_count": db.get("revision_count", 0),
        "verdict": db.get("claude_verdict") or "APPROVED",
        "tokens": db.get("total_tokens", 0),
        "backend": backend,
        "frontend": frontend,
        "notes": db.get("notes") or "",
    }


def _json_to_db_payload(entry: dict) -> dict:
    """Convert a reports.json entry to HandoffRun create payload."""
    backend = entry.get("backend") or {}
    frontend = entry.get("frontend") or {}

    mode = entry.get("mode")
    if not mode:
        if backend and frontend:
            mode = "full"
        elif backend:
            mode = "backend-only"
        elif frontend:
            mode = "frontend-only"
        else:
            mode = "full"

    issues_parts = []
    if backend.get("issues") and backend["issues"] != "none":
        issues_parts.append(backend["issues"])
    if frontend.get("issues") and frontend["issues"] != "none":
        issues_parts.append(frontend["issues"])

    return {
        "feature": entry.get("feature", ""),
        "mode": mode,
        "status": entry.get("status", "success"),
        "run_date": (entry.get("date") or "2026-01-01") + "T00:00:00Z",
        "backend_files": backend.get("files_written") if backend else None,
        "frontend_files": frontend.get("files_written") if frontend else None,
        "claude_verdict": entry.get("verdict"),
        "revision_count": entry.get("revision_count", 0),
        "total_tokens": entry.get("tokens") if isinstance(entry.get("tokens"), int) else 0,
        "issues": " | ".join(issues_parts) if issues_parts else None,
        "author": "Claude Code",
        "notes": entry.get("notes") or "Imported from docs/reports.json",
    }


def main():
    if not REPORTS_PATH.exists():
        print(f"Not found: {REPORTS_PATH}")
        sys.exit(1)

    json_entries: list[dict] = json.loads(REPORTS_PATH.read_text())
    json_by_feature = {e["feature"]: e for e in json_entries}

    headers = {"Authorization": f"Bearer {_get_token()}"}
    db_runs = _fetch_all_db(headers)
    db_by_feature = {r["feature"]: r for r in db_runs}

    json_to_db = 0
    db_to_json = 0
    json_changed = False

    # 1. JSON → DB
    for feature, entry in json_by_feature.items():
        if feature not in db_by_feature:
            payload = _json_to_db_payload(entry)
            res = requests.post(
                f"{API_BASE}/dev/dev_handoff_runs",
                json=payload,
                headers=headers,
                timeout=5,
            )
            if res.status_code in (200, 201):
                db_id = res.json().get("id")
                entry["id"] = db_id  # update JSON id to match DB id
                json_changed = True
                json_to_db += 1
                print(f"  + JSON→DB  [{db_id}] {feature[:60]}")
            else:
                print(f"  x Failed   {feature[:60]}: {res.status_code} {res.text[:100]}")

    # 2. DB → JSON
    next_id = max((e.get("id") or 0 for e in json_entries), default=0) + 1
    for feature, db_run in db_by_feature.items():
        if feature not in json_by_feature:
            entry = _db_to_json(db_run)
            if not entry.get("id"):
                entry["id"] = next_id
                next_id += 1
            json_entries.append(entry)
            json_by_feature[feature] = entry
            json_changed = True
            db_to_json += 1
            print(f"  + DB→JSON  [{entry['id']}] {feature[:60]}")

    # 3. Save JSON if changed
    if json_changed:
        json_entries.sort(key=lambda e: e.get("id") or 0)
        REPORTS_PATH.write_text(json.dumps(json_entries, indent=2))
        print(f"\nSaved {REPORTS_PATH} ({len(json_entries)} entries)")

    print(f"\nDone. JSON→DB: {json_to_db}  DB→JSON: {db_to_json}  unchanged: {len(json_by_feature) - json_to_db}")


if __name__ == "__main__":
    main()
