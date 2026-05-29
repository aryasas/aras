import pytest

def test_plan_list_public(client, db):
    # Seed a plan first
    from apps.saas.models import Plan
    plan = Plan(plan_key="free", name="Free Plan", price=0)
    db.add(plan)
    db.flush()

    resp = client.get("/api/v1/saas/plans/public")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["plan_key"] == "free"

def test_subscription_create(auth_client, db):
    # Need a plan first
    from apps.saas.models import Plan
    plan = Plan(plan_key="lite", name="Lite Plan", price=100000)
    db.add(plan)
    db.flush()

    resp = auth_client.post("/api/v1/saas/subscription", json={
        "email": "test@example.com",
        "company_name": "Test Company",
        "plan_id": plan.id,
        "status": "pending"
    })
    assert resp.status_code == 201
    assert resp.json()["data"]["company_name"] == "Test Company"
