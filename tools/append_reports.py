#!/usr/bin/env python3
"""
Parse docs/handoff.md Agent Reports section and append APPROVED reports to docs/reports.json.

Usage:
  python tools/append_reports.py

Only appends if:
1. Claude Review verdict = APPROVED
2. Agent Reports section exists with both Backend + Frontend data
3. docs/reports.json exists (or creates if missing)

Output: appended report in docs/reports.json, cleanup handoff.md comments
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent
HANDOFF_FILE = PROJECT_ROOT / "docs" / "handoff.md"
REPORTS_FILE = PROJECT_ROOT / "docs" / "reports.json"


def parse_handoff(content: str) -> Optional[Dict[str, Any]]:
    """Extract Claude Review verdict, date, and Agent Reports from handoff.md."""
    result = {
        "verdict": None,
        "date": None,
        "feature": None,
        "revision_count": 0,
        "backend": {},
        "frontend": {},
    }

    # Extract feature
    for line in content.splitlines():
        if line.startswith("> Feature:"):
            result["feature"] = line.replace("> Feature:", "").strip()
            break

    # Find latest Claude Review section
    sections = content.split("## Claude Review")
    if len(sections) < 2:
        return None

    latest_review = sections[-1]
    for line in latest_review.splitlines():
        if "verdict:" in line:
            result["verdict"] = line.split("verdict:")[-1].strip().lstrip("<!-").rstrip("->").strip()
        if "date:" in line:
            result["date"] = line.split("date:")[-1].strip().lstrip("<!-").rstrip("->").strip()

    if result["verdict"] != "APPROVED":
        return None

    # Count revision cycles (Agent Reports (revision ...))
    result["revision_count"] = content.count("## Agent Reports (revision")

    # Parse latest Agent Reports section (before latest Claude Review)
    reports_section = sections[-2]  # content before last "## Claude Review"

    # Find Backend section
    backend_match = re.search(r"### Backend.*?\n([\s\S]*?)(?=### Frontend|$)", reports_section)
    if backend_match:
        result["backend"] = _parse_report_block(backend_match.group(1))

    # Find Frontend section
    frontend_match = re.search(r"### Frontend.*?\n([\s\S]*?)(?=##|$)", reports_section)
    if frontend_match:
        result["frontend"] = _parse_report_block(frontend_match.group(1))

    return result if (result["backend"] or result["frontend"]) else None


def _parse_report_block(block: str) -> dict:
    """Parse individual report block (Backend or Frontend)."""
    report = {
        "files_written": "none",
        "features_added": "none",
        "fixes_applied": "none",
        "framework_changes": "none",
        "issues": "none",
    }
    for line in block.splitlines():
        m = re.match(r"-\s+(\w+):\s*(.+)", line.strip())
        if m and m.group(1) in report:
            report[m.group(1)] = m.group(2).strip()
    return report


def load_reports() -> list:
    """Load existing reports.json or return empty list."""
    if REPORTS_FILE.exists():
        try:
            return json.loads(REPORTS_FILE.read_text())
        except json.JSONDecodeError:
            return []
    return []


def append_report(parsed: dict) -> bool:
    """Append approved report to docs/reports.json."""
    if not parsed:
        print("  x No APPROVED report found in handoff.md")
        return False

    reports = load_reports()

    # Generate ID (next sequential)
    next_id = max((r.get("id", 0) for r in reports), default=0) + 1

    new_report = {
        "id": next_id,
        "date": parsed["date"] or datetime.now().strftime("%Y-%m-%d"),
        "feature": parsed["feature"] or "Unknown",
        "revision_count": parsed["revision_count"],
        "backend": parsed["backend"],
        "frontend": parsed["frontend"],
        "verdict": parsed["verdict"],
    }

    reports.append(new_report)
    REPORTS_FILE.write_text(json.dumps(reports, indent=2))

    print(f"  + Report #{next_id} appended to docs/reports.json")
    print(f"    Feature: {new_report['feature']}")
    print(f"    Date: {new_report['date']}")
    print(f"    Revision: {new_report['revision_count']}")

    return True


def main():
    if not HANDOFF_FILE.exists():
        print(f"ERROR: {HANDOFF_FILE} not found")
        return False

    handoff_content = HANDOFF_FILE.read_text()
    parsed = parse_handoff(handoff_content)

    if not parsed:
        print("  x Handoff verdict is not APPROVED, or reports missing. Skipping.")
        return False

    return append_report(parsed)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
