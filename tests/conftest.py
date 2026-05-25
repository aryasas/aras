import os
import sys
from pathlib import Path

import pytest

collect_ignore = [
    str(Path(__file__).parent / "test_api.py"),
    str(Path(__file__).parent / "test_api2.py"),
    str(Path(__file__).parent / "test_options.py"),
    str(Path(__file__).parent / "test_via_requests.py"),
]
from fastapi.testclient import TestClient

# Wire api/ onto sys.path so `from core import Aras` and `from main import app` resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

os.environ.setdefault("DATABASE_URL", os.environ.get("DATABASE_URL", "postgresql://aras:999999@localhost:5432/arastest"))
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("ARAS_ADMIN_PASSWORD", "admin")
os.environ.setdefault("ARAS_MODE", "development")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")
os.environ.setdefault("APP_NAME", "Aras Test")


@pytest.fixture(scope="session")
def client():
    from main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def admin_token(client):
    resp = client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "admin"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
