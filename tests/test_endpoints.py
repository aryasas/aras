"""
Smoke tests for core API endpoints.
Requires client + admin_headers fixtures from conftest.py.
"""


def test_login_returns_token(client):
    resp = client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "admin"}
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password_rejected(client):
    resp = client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "wrongpassword"},
    )
    assert resp.status_code in (400, 401, 422)


def test_dev_sync_requires_auth(client):
    resp = client.post("/api/v1/dev/sync")
    assert resp.status_code == 401


def test_dev_sync_with_auth(client, admin_headers):
    resp = client.post("/api/v1/dev/sync", headers=admin_headers)
    assert resp.status_code == 200


def test_sidebar_requires_auth(client):
    assert client.get("/api/v1/sidebar").status_code == 401


def test_sidebar_with_auth(client, admin_headers):
    resp = client.get("/api/v1/sidebar", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
