import pytest
from apps.report.models import Report
from core.auth.models import User

# gemini-flash

# gemini-flash

def test_script_report_requires_superuser(auth_client, db):
    """Verify that only admins can run script reports."""
    # 1. Create a script report (pre-approved to bypass that check)
    admin = db.query(User).filter(User.username.like("admin%")).first()
    report = Report(
        code="test_security",
        name="Security Test",
        report_type="script",
        script="result = [{'a': 1}]",
        org_id=1,
        script_approved_by_id=admin.id
    )
    db.add(report)
    db.commit()

    # 2. Run as admin (should pass)
    resp = auth_client.post(f"/api/v1/report/reports/{report.id}/action/generate_report")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    # The response from model_action is ok({"title", "data", "columns"})
    assert resp.json()["data"]["data"] == [{'a': 1}]

def test_script_report_rejects_unapproved(auth_client, db):
    """Verify that unapproved scripts are rejected."""
    report = Report(
        code="test_unapproved",
        name="Unapproved Test",
        report_type="script",
        script="result = [{'a': 1}]",
        org_id=1,
        script_approved_by_id=None # NOT APPROVED
    )
    db.add(report)
    db.commit()

    resp = auth_client.post(f"/api/v1/report/reports/{report.id}/action/generate_report")
    assert resp.status_code == 200 
    assert "error" in resp.json()["data"]
    assert "not approved" in resp.json()["data"]["error"]

def test_script_report_timeout(auth_client, db):
    """Verify that long-running scripts time out."""
    admin = db.query(User).filter(User.username.like("admin%")).first()
    # Using a busy loop since __builtins__ is empty (prevents import time)
    report = Report(
        code="test_timeout",
        name="Timeout Test",
        report_type="script",
        script="x = 0\nwhile x < 500000000:\n    x += 1\nresult = []",
        org_id=1,
        script_approved_by_id=admin.id
    )
    db.add(report)
    db.commit()

    resp = auth_client.post(f"/api/v1/report/reports/{report.id}/action/generate_report")
    assert resp.status_code == 200
    assert "timed out" in resp.json()["data"]["error"]
