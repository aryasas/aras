from datetime import datetime, timezone

from core.auth.models import User
from core.auth.service import create_access_token
from core.registry.activity_log import ActivityLog
from apps.saas.models import Subscription
from apps.saas.services.email import ensure_marketing_consent


# gpt-5
def test_user_anonymize_self_preserves_audit_rows(db):
    user = User(
        username="keepme",
        name="Alice Example",
        email="alice@example.com",
        password_hash=User.hash_password("password123"),
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log = ActivityLog(
        resource=user.__tablename__,
        resource_id=user.id,
        action="INSERT",
        changes={"email": [None, "[redacted]"]},
        user_id=user.id,
    )
    db.add(log)
    db.commit()

    before_count = db.query(ActivityLog).count()
    user.anonymize_self(db, user_id=user.id)
    db.commit()
    db.refresh(user)

    tombstone = f"[erased:{user.__tablename__}:{user.id}]"
    assert user.name == tombstone
    assert user.email == tombstone
    assert user.deleted_at is not None
    assert user.username == "keepme"
    assert user.is_admin is False
    assert db.query(ActivityLog).count() == before_count


# gpt-5
def test_erase_me_route_present_and_erases_current_user(client, db):
    user = User(
        username="erase.me@example.com",
        name="Erase Me",
        email="erase.me@example.com",
        password_hash=User.hash_password("password123"),
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.username, "purpose": "access"})
    response = client.post("/api/v1/auth/erase-me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["data"] == {"erased": True}

    db.refresh(user)
    assert user.email == f"[erased:{user.__tablename__}:{user.id}]"
    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    assert "/api/v1/auth/erase-me" in openapi.json()["paths"]


# gpt-5
def test_marketing_consent_guard_and_signup_fields(db):
    allowed = Subscription(
        email="consented@example.com",
        company_name="Consent Co",
        marketing_consent=True,
        consent_at=datetime.now(timezone.utc),
    )
    denied = Subscription(
        email="blocked@example.com",
        company_name="No Consent Co",
        marketing_consent=False,
        consent_at=None,
    )
    db.add_all([allowed, denied])
    db.commit()

    assert ensure_marketing_consent(allowed) is True
    assert ensure_marketing_consent(denied) is False
    assert "marketing_consent" in User.__table__.c
    assert "consent_at" in User.__table__.c
    assert "marketing_consent" in Subscription.__table__.c
    assert "consent_at" in Subscription.__table__.c
