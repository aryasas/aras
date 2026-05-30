import pytest
from fastapi.testclient import TestClient
import os

@pytest.fixture
def override_role():
    original = os.environ.get("ARAS_ROLE")
    def _override(role):
        os.environ["ARAS_ROLE"] = role
        # We need to reload main but TestClient already mounted routes based on env at import time.
        # Actually testing dynamic routing based on env var at runtime is tricky if the router is mounted conditionally at startup.
        # We can just test the current loaded app's routes.
    yield _override
    if original is not None:
        os.environ["ARAS_ROLE"] = original
    else:
        if "ARAS_ROLE" in os.environ:
            del os.environ["ARAS_ROLE"]

def test_control_panel_routes(client: TestClient, admin_user, auth_headers):
    # This assumes ARAS_ROLE="tenant" (default) during tests
    headers = auth_headers(admin_user)
    res = client.get("/api/v1/saas/control-panel/tenants", headers=headers)
    assert res.status_code == 404
