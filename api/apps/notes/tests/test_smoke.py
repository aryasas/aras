import pytest
from core.aras import Aras

def test_note_crud(auth_client):
    # Create
    resp = auth_client.post("/api/v1/notes/note", json={"title": "Test Note", "body": "Test Body"})
    assert resp.status_code == 201
    note_id = resp.json()["data"]["id"]

    # List
    resp = auth_client.get("/api/v1/notes/note")
    assert resp.status_code == 200
    assert any(n["id"] == note_id for n in resp.json()["data"]["items"])

    # Get
    resp = auth_client.get(f"/api/v1/notes/note/{note_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["title"] == "Test Note"

    # Update
    resp = auth_client.put(f"/api/v1/notes/note/{note_id}", json={"title": "Updated Note", "body": "Updated Body"})
    assert resp.status_code == 200
    assert resp.json()["data"]["title"] == "Updated Note"

    # Delete
    resp = auth_client.delete(f"/api/v1/notes/note/{note_id}")
    assert resp.status_code == 200

    # Verify deleted
    resp = auth_client.get(f"/api/v1/notes/note/{note_id}")
    assert resp.status_code == 404

def test_note_rbac_denial(client, db, auth_headers):
    # Create a non-admin user with no permissions
    user = Aras.User(
        username="no_perm_user",
        email="no_perm@aras.local",
        password_hash=Aras.User.hash_password("password123"),
        is_admin=False
    )
    db.add(user)
    db.flush()
    
    headers = auth_headers(user)
    resp = client.post("/api/v1/notes/note", json={"title": "Fail Note"}, headers=headers)
    # Aras returns 403 for RBAC denial
    assert resp.status_code == 403

def test_note_scope_leak_attempt(auth_client, db):
    # Notes are not currently scoped by org, but let's test if we can 
    # force a different user_id if we were scoped (simulation)
    # First create a note as admin
    resp = auth_client.post("/api/v1/notes/note", json={"title": "Admin Note"})
    note_data = resp.json()["data"]
    
    # Try to update created_by (should be ignored or rejected depending on framework)
    resp = auth_client.patch(f"/api/v1/notes/note/{note_data['id']}", json={"created_by": 999})
    assert resp.status_code == 200
    # Framework should NOT allow overriding system fields like created_by
    assert resp.json()["data"]["created_by"] != 999
