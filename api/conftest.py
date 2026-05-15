import os
import sys

import pytest
from fastapi.testclient import TestClient

# Ensure api/ is on the path when running pytest from the project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Override settings before importing the app
os.environ.setdefault("ARAS_MODE", "testing")


@pytest.fixture(scope="session")
def client():
    from main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def admin_token(client):
    resp = client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "testadmin123"}
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
