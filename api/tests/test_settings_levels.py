from core.registry.settings_service import SettingsService
from core.registry.sys_settings import Settings


def test_settings_service_persists_registry_level(db):
    SettingsService.set(db, "core", "site_name", "Aras Test")
    SettingsService.set(db, "admin", "retention_days", 90)
    db.flush()

    framework_row = db.query(Settings).filter_by(
        namespace="core",
        key="site_name",
        level="framework",
    ).first()
    admin_row = db.query(Settings).filter_by(
        namespace="admin",
        key="retention_days",
        level="admin",
    ).first()

    assert framework_row is not None
    assert admin_row is not None
    assert db.query(Settings).filter_by(namespace="core", key="site_name", level="app").first() is None


def test_settings_namespace_api_returns_level_metadata(auth_client):
    response = auth_client.get("/api/v1/settings")
    assert response.status_code == 200

    payload = response.json()["data"]
    by_name = {item["name"]: item for item in payload}

    assert by_name["core"]["level"] == "framework"
    assert by_name["core_config"]["level"] == "framework"
    assert by_name["admin"]["level"] == "admin"
    assert by_name["admin"]["section_count"] >= 1


def test_settings_namespace_api_filters_by_level(auth_client):
    response = auth_client.get("/api/v1/settings?level=admin")
    assert response.status_code == 200

    payload = response.json()["data"]
    assert payload
    assert all(item["level"] == "admin" for item in payload)
