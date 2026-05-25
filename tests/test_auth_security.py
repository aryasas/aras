"""
Framework security tests: authentication and RBAC enforcement.
Run from api/: pytest ../tests/test_auth_security.py
"""


def test_admin_endpoints_require_auth(client):
    assert client.get("/api/v1/admin/apps").status_code == 401
    assert client.delete("/api/v1/admin/uninstall/someapp").status_code == 401


def test_dev_endpoints_require_auth(client):
    assert client.post("/api/v1/dev/sync").status_code == 401
    assert client.get("/api/v1/dev/info").status_code == 401
    assert client.get("/api/v1/dev/stats").status_code == 401
    assert client.get("/api/v1/dev/inspect/env").status_code == 401
    assert client.get("/api/v1/dev/inspect/routes").status_code == 401
    assert client.get("/api/v1/dev/inspect/models").status_code == 401


def test_sidebar_requires_auth(client):
    assert client.get("/api/v1/sidebar").status_code == 401


def test_login_with_env_password(client):
    resp = client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "admin"}
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_admin_can_access_admin_endpoints(client, admin_headers):
    assert client.get("/api/v1/admin/apps", headers=admin_headers).status_code == 200


def test_admin_can_access_dev_endpoints(client, admin_headers):
    assert client.get("/api/v1/dev/info", headers=admin_headers).status_code == 200
    assert client.get("/api/v1/dev/inspect/env", headers=admin_headers).status_code == 200


def test_admin_can_access_sidebar(client, admin_headers):
    resp = client.get("/api/v1/sidebar", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_query_requires_auth_for_non_public_resource(client):
    resp = client.post("/api/v1/auth_users/query", json={"filters": []})
    assert resp.status_code == 401


def test_private_metadata_requires_auth(client):
    # auth_users is private (not marked __public_read__)
    resp = client.get("/api/v1/metadata/auth_users")
    assert resp.status_code == 401


def test_public_metadata_is_accessible_without_auth(client):
    # sys_settings is marked __public_read__ = True
    resp = client.get("/api/v1/metadata/sys_settings")
    assert resp.status_code in (200, 404)  # 404 if resource not registered, not 401
