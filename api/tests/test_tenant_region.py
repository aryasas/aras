# gemini-3-flash-preview
import pytest
from unittest.mock import MagicMock, patch
from core.tenant.provisioner import provision_tenant
from core.tenant.registry import tenant_registry
import os

# gemini-3-flash-preview
def test_provision_tenant_records_region():
    """Test that provisioning a tenant records the specified region."""
    tenant_id = "test-region-tenant"
    db_name = "test_region_db"
    region = "eu"
    
    # Mock admin connection and DB creation
    with patch("core.tenant.provisioner._get_admin_connection") as mock_admin, \
         patch("core.tenant.provisioner.create_engine") as mock_engine, \
         patch("alembic.command.stamp") as mock_stamp, \
         patch("core.tenant.provisioner.install_app_on_tenant") as mock_install, \
         patch("core.logic.discovery.discover_apps"):

        mock_conn = MagicMock()
        mock_admin.return_value.connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = None # DB doesn't exist

        
        # provision_tenant signature: (tenant_id, db_name, apps, extra, region)
        provision_tenant(tenant_id, db_name, region=region)
        
        # Verify it's in the registry with the correct region
        info = tenant_registry.get(tenant_id)
        assert info is not None
        assert info["region"] == region
        
        # Cleanup
        tenant_registry.unregister(tenant_id)

# gemini-3-flash-preview
def test_provision_tenant_defaults_region():
    """Test that provisioning a tenant defaults to 'sea' (or env default) when unspecified."""
    tenant_id = "test-default-region-tenant"
    db_name = "test_default_region_db"
    
    # Mock admin connection and DB creation
    with patch("core.tenant.provisioner._get_admin_connection") as mock_admin, \
         patch("core.tenant.provisioner.create_engine") as mock_engine, \
         patch("alembic.command.stamp") as mock_stamp, \
         patch("core.tenant.provisioner.install_app_on_tenant") as mock_install, \
         patch("core.logic.discovery.discover_apps"):

        mock_conn = MagicMock()
        mock_admin.return_value.connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = None # DB doesn't exist

        
        # Ensure default region env is set for test consistency
        with patch.dict(os.environ, {"TENANT_DEFAULT_REGION": "sea"}):
            provision_tenant(tenant_id, db_name)
        
        # Verify it's in the registry with default region
        info = tenant_registry.get(tenant_id)
        assert info is not None
        assert info["region"] == "sea"
        
        # Cleanup
        tenant_registry.unregister(tenant_id)

# gemini-3-flash-preview
def test_migration_0006_single_head():
    """Verify alembic migration history has a single head ending at 0006."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    
    api_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    config = Config(os.path.join(api_root, "alembic.ini"))
    config.set_main_option("script_location", os.path.join(api_root, "alembic"))
    
    script = ScriptDirectory.from_config(config)
    heads = script.get_heads()
    
    assert len(heads) == 1
    assert heads[0] == "20260605_0006"
