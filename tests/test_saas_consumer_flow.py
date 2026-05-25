import uuid


def _plans_by_name(client):
    response = client.get("/api/v1/saas/plans/public")
    assert response.status_code == 200, response.text
    return {plan["name"]: plan for plan in response.json()}


def _register_subscribe_pay(client, email: str, company: str, plan_id: int):
    register = client.post("/api/v1/saas/portal/register", json={
        "email": email,
        "password": "consumer-password",
        "company_name": company,
        "full_name": "Consumer User",
        "plan_id": plan_id,
    })
    assert register.status_code == 200, register.text
    token = register.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    subscribe = client.post(
        "/api/v1/saas/portal/subscribe",
        json={"plan_id": plan_id},
        headers=headers,
    )
    assert subscribe.status_code == 200, subscribe.text
    assert subscribe.json()["plan"]["id"] == plan_id

    payment = client.post(
        "/api/v1/saas/portal/payment/dev-bypass",
        json={"provider": "dev", "reference": f"test-{plan_id}"},
        headers=headers,
    )
    assert payment.status_code == 200, payment.text
    assert payment.json()["status"] == "active"
    assert payment.json()["payment"]["bypassed"] is True
    assert payment.json()["license_token"]
    return headers


def test_consumer_register_subscribe_dev_payment_and_plan_app_access(client):
    suffix = uuid.uuid4().hex[:8]
    plans = _plans_by_name(client)
    starter = plans["Starter"]
    business = plans["Business"]
    enterprise = plans["Enterprise"]

    assert starter["features"]["apps"] == ["accounting", "party", "report"]
    assert "stock" in business["features"]["apps"]
    assert {"crm", "hr", "asset"}.issubset(set(enterprise["features"]["apps"]))

    basic_headers = _register_subscribe_pay(
        client,
        f"basic-{suffix}@example.test",
        f"Basic Co {suffix}",
        starter["id"],
    )
    pro_headers = _register_subscribe_pay(
        client,
        f"pro-{suffix}@example.test",
        f"Pro Co {suffix}",
        business["id"],
    )

    basic_apps = client.get("/api/v1/saas/portal/apps", headers=basic_headers)
    assert basic_apps.status_code == 200, basic_apps.text
    basic_names = {app["name"] for app in basic_apps.json()["apps"]}
    assert "accounting" in basic_names
    assert "stock" not in basic_names
    assert "crm" not in basic_names

    pro_apps = client.get("/api/v1/saas/portal/apps", headers=pro_headers)
    assert pro_apps.status_code == 200, pro_apps.text
    pro_names = {app["name"] for app in pro_apps.json()["apps"]}
    assert {"accounting", "stock", "pot"}.issubset(pro_names)
    assert "crm" not in pro_names


def test_consumer_cannot_view_apps_before_payment(client):
    suffix = uuid.uuid4().hex[:8]
    plan_id = _plans_by_name(client)["Starter"]["id"]

    register = client.post("/api/v1/saas/portal/register", json={
        "email": f"pending-{suffix}@example.test",
        "password": "consumer-password",
        "company_name": f"Pending Co {suffix}",
        "full_name": "Pending User",
        "plan_id": plan_id,
    })
    assert register.status_code == 200, register.text
    headers = {"Authorization": f"Bearer {register.json()['token']}"}

    apps = client.get("/api/v1/saas/portal/apps", headers=headers)
    assert apps.status_code == 402
