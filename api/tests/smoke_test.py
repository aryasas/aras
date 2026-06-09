import pytest

def test_root_is_alive(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_landing_page_list(client):
    response = client.get("/api/v1/web/landing")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_quick_actions_requires_auth(client):
    response = client.get("/api/v1/admin/quick-actions")
    assert response.status_code == 401

def test_quick_actions_list(auth_client):
    response = auth_client.get("/api/v1/admin/quick-actions")
    assert response.status_code == 200
    actions = response.json()
    assert isinstance(actions, list)
    # Verify standard routes are present
    labels = [a["label"] for a in actions]
    assert "Dashboard" in labels
    assert "Administration" in labels

def test_landing_section_detail_404(client):
    response = client.get("/api/v1/web/landing/nonexistent_key")
    assert response.status_code == 404
