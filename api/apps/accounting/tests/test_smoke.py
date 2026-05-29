import pytest

def test_account_crud(auth_client, org):
    # Create
    resp = auth_client.post("/api/v1/accounting/accounts", json={
        "name": "Cash",
        "code": "1001",
        "account_type": "asset_current",
        "org_id": org.id
    })
    assert resp.status_code == 201
    acc_id = resp.json()["data"]["id"]

    # Get
    resp = auth_client.get(f"/api/v1/accounting/accounts/{acc_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "Cash"

    # Update
    resp = auth_client.put(f"/api/v1/accounting/accounts/{acc_id}", json={
        "name": "Petty Cash",
        "code": "1001",
        "account_type": "asset_current",
        "org_id": org.id
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "Petty Cash"

def test_account_m2m_invalid_ids(auth_client, org):
    # Create an account
    resp = auth_client.post("/api/v1/accounting/accounts", json={
        "name": "Main Account",
        "code": "1000",
        "account_type": "asset_current",
        "org_id": org.id
    })
    acc_id = resp.json()["data"]["id"]

    # Try to update M2M with invalid ID (99999)
    resp = auth_client.put(f"/api/v1/accounting/accounts/{acc_id}/related_accounts", json=[99999])
    # Framework maps ValidationException to 422
    assert resp.status_code == 422
    assert "Some target IDs are invalid or out of scope" in resp.json()["error"]["message"]
