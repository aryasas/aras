import uuid


def _scoped_user_setup():
    from apps.config.erp_rbac import ErpUserAccess, ensure_erp_role
    from core.auth.models import User
    from core.lib.database import SessionLocal
    from core.registry.permission import Permission
    from core.registry.role import Role
    from core.registry.user_role import UserRole
    from sqlalchemy import text

    suffix = uuid.uuid4().hex[:8]
    email = f"scope-{suffix}@example.test"
    password = "scope-password"

    db = SessionLocal()
    try:
        org_a_id = db.execute(
            text(
                "INSERT INTO erp_config_organizations "
                "(name, code, profile, unit_type, is_group, is_default, fiscal_year_start_month, "
                "default_charge_enable, enable_perpetual_inventory, enable_provisional_non_stock, "
                "avg_cost_by_location, allow_zero_stock, stock_valuation_method, date_format, "
                "number_format, decimal_precision) "
                "VALUES (:name, :code, 'general', 'organization', false, false, 1, false, false, "
                "false, false, false, 'FIFO', 'DD/MM/YYYY', '#,###.##', 2) RETURNING id"
            ),
            {"name": f"Scope Org A {suffix}", "code": f"SOA{suffix[:6]}"},
        ).scalar_one()
        org_b_id = db.execute(
            text(
                "INSERT INTO erp_config_organizations "
                "(name, code, profile, unit_type, is_group, is_default, fiscal_year_start_month, "
                "default_charge_enable, enable_perpetual_inventory, enable_provisional_non_stock, "
                "avg_cost_by_location, allow_zero_stock, stock_valuation_method, date_format, "
                "number_format, decimal_precision) "
                "VALUES (:name, :code, 'general', 'organization', false, false, 1, false, false, "
                "false, false, false, 'FIFO', 'DD/MM/YYYY', '#,###.##', 2) RETURNING id"
            ),
            {"name": f"Scope Org B {suffix}", "code": f"SOB{suffix[:6]}"},
        ).scalar_one()
        account_a_id = db.execute(
            text(
                "INSERT INTO erp_accounting_accounts "
                "(org_id, name, code, account_type, is_shared, is_group) "
                "VALUES (:org_id, :name, :code, :account_type, true, false) RETURNING id"
            ),
            {
                "org_id": org_a_id,
                "name": f"Scoped Cash {suffix}",
                "code": f"A{suffix[:6]}",
                "account_type": "asset_current",
            },
        ).scalar_one()
        account_b_id = db.execute(
            text(
                "INSERT INTO erp_accounting_accounts "
                "(org_id, name, code, account_type, is_shared, is_group) "
                "VALUES (:org_id, :name, :code, :account_type, true, false) RETURNING id"
            ),
            {
                "org_id": org_b_id,
                "name": f"Foreign Cash {suffix}",
                "code": f"B{suffix[:6]}",
                "account_type": "asset_current",
            },
        ).scalar_one()

        user = User(
            username=email,
            email=email,
            password_hash=User.hash_password(password),
            is_active=True,
            is_admin=False,
        )
        db.add(user)
        db.flush()

        role = Role(name=f"Scope Test {suffix}", description="Cross-org regression role")
        db.add(role)
        db.flush()
        for action in ("READ", "CREATE", "UPDATE", "DELETE"):
            db.add(Permission(role_id=role.id, resource="erp_accounting_accounts", action=action))
        db.add(UserRole(user_id=user.id, role_id=role.id))

        erp_role = ensure_erp_role(db)
        db.add(ErpUserAccess(user_id=user.id, role_id=erp_role.id, org_id=org_a_id))

        db.commit()
        return {
            "email": email,
            "password": password,
            "org_a_id": org_a_id,
            "org_b_id": org_b_id,
            "account_a_id": account_a_id,
            "account_b_id": account_b_id,
            "suffix": suffix,
        }
    finally:
        db.close()


def _login(client, email: str, password: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/token", data={"username": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_cross_org_scope_applies_to_crud_query_and_batch(client, admin_headers):
    data = _scoped_user_setup()
    headers = _login(client, data["email"], data["password"])

    listed = client.get("/api/v1/accounting/accounts", headers=headers)
    assert listed.status_code == 200, listed.text
    listed_ids = {item["id"] for item in listed.json()["data"]["items"]}
    assert data["account_a_id"] in listed_ids
    assert data["account_b_id"] not in listed_ids

    query = client.post(
        "/api/v1/erp_accounting_accounts/query",
        headers=headers,
        json={"filters": [{"field": "name", "op": "contains", "value": "Cash"}]},
    )
    assert query.status_code == 200, query.text
    query_ids = {item["id"] for item in query.json()["items"]}
    assert data["account_a_id"] in query_ids
    assert data["account_b_id"] not in query_ids

    foreign_get = client.get(f"/api/v1/accounting/accounts/{data['account_b_id']}", headers=headers)
    assert foreign_get.status_code == 404

    foreign_scope = client.get(
        "/api/v1/accounting/accounts",
        headers={**headers, "X-Org-ID": str(data["org_b_id"])},
    )
    assert foreign_scope.status_code == 403

    created = client.post(
        "/api/v1/accounting/accounts",
        headers=headers,
        json={
            "name": f"Injected Scope {data['suffix']}",
            "code": f"C{data['suffix'][:6]}",
            "account_type": "asset_current",
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["data"]["org_id"] == data["org_a_id"]

    batch = client.post(
        "/api/v1/accounting/accounts/batch-delete",
        headers=headers,
        json={"ids": [data["account_a_id"], data["account_b_id"]]},
    )
    assert batch.status_code == 404

    admin_a = client.get(f"/api/v1/accounting/accounts/{data['account_a_id']}", headers=admin_headers)
    admin_b = client.get(f"/api/v1/accounting/accounts/{data['account_b_id']}", headers=admin_headers)
    assert admin_a.status_code == 200
    assert admin_b.status_code == 200
