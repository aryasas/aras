def test_custom_sql_report_type_is_rejected(client, admin_headers):
    """Raw SQL reports are not a supported report type."""
    resp = client.post(
        "/api/v1/report/reports",
        json={
            "code": "bad_sql",
            "name": "Bad SQL",
            "report_type": "custom_sql",
            "script": "SELECT * FROM invoices WHERE org_id = :org_id",
            "org_id": 1,
        },
        headers={**admin_headers, "X-Org-ID": "1"},
    )
    assert resp.status_code in (400, 422)


def test_report_execute_requires_org_context(client, admin_headers):
    """Reports must not execute without a selected/validated organization."""
    resp = client.get("/api/v1/report/execute/stock_summary", headers=admin_headers)
    assert resp.status_code == 400


def test_report_execute_uses_canonical_non_erp_path(client, admin_headers):
    """The legacy /erp report path is not mounted."""
    legacy_path = "/api/v1/report/" + "erp/report/execute/stock_summary"
    legacy = client.get(legacy_path, headers={**admin_headers, "X-Org-ID": "1"})
    assert legacy.status_code == 404

    canonical = client.get("/api/v1/report/execute/stock_summary", headers={**admin_headers, "X-Org-ID": "1"})
    assert canonical.status_code in (200, 404)
