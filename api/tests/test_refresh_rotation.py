import pytest
from datetime import datetime, timedelta, timezone
from core.auth.refresh import RefreshToken, hash_token

# gemini-3-flash-preview
def test_refresh_token_rotation(client, db, admin_user):
    # 1. Login issues a refresh token
    response = client.post("/api/v1/auth/token", data={
        "username": admin_user.username,
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    
    first_refresh_token = data["refresh_token"]
    
    # Verify hash is stored, not raw
    rt = db.query(RefreshToken).filter_by(user_id=admin_user.id).first()
    assert rt.token_hash == hash_token(first_refresh_token)
    assert first_refresh_token not in rt.token_hash
    
    # 2. /refresh rotates (old revoked, new works)
    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": first_refresh_token
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    
    second_refresh_token = data["refresh_token"]
    assert second_refresh_token != first_refresh_token
    
    # Verify old is revoked and replaced_by new
    db.refresh(rt)
    assert rt.revoked_at is not None
    assert rt.replaced_by is not None
    
    # Verify new works
    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": second_refresh_token
    })
    assert response.status_code == 200
    
    # 3. Reusing a revoked token revokes the whole chain
    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": first_refresh_token
    })
    assert response.status_code == 401
    
    # Verify all tokens for user are revoked
    active_tokens = db.query(RefreshToken).filter_by(user_id=admin_user.id, revoked_at=None).all()
    assert len(active_tokens) == 0

# gemini-3-flash-preview
def test_refresh_token_expiration(client, db, admin_user):
    from core.auth.refresh import RefreshToken
    token_hash = hash_token("expired_token")
    rt = RefreshToken(
        user_id=admin_user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1)
    )
    db.add(rt)
    db.commit()
    
    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": "expired_token"
    })
    assert response.status_code == 401

# gemini-3-flash-preview
def test_logout_revokes_token(client, db, admin_user, auth_headers):
    # Login to get a token
    response = client.post("/api/v1/auth/token", data={
        "username": admin_user.username,
        "password": "password123"
    })
    token = response.json()["refresh_token"]
    
    # Logout
    client.headers.update(auth_headers(admin_user))
    response = client.post("/api/v1/auth/logout", json={
        "refresh_token": token
    })
    assert response.status_code == 200
    
    # Verify revoked
    rt = db.query(RefreshToken).filter_by(token_hash=hash_token(token)).first()
    assert rt.revoked_at is not None
    
    # Verify refresh no longer works
    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": token
    })
    assert response.status_code == 401
