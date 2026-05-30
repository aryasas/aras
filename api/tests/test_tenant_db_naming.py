import pytest
import re
from unittest.mock import patch, MagicMock
from core.tenant.service import provision_tenant

# gemini-2-5-flash

def test_provision_tenant_db_naming():
    """Assert provision_tenant() produces a DB name matching ^tenant_[a-zA-Z0-9_-]+$ by default."""
    tenant_id = "test-tenant"
    
    # We mock the low-level provisioner that actually creates the DB
    with patch("core.tenant.service._provision_tenant") as mock_provision:
        mock_provision.return_value = {"tenant_id": tenant_id, "db_name": f"tenant_{tenant_id}"}
        
        # Call with default db_name
        provision_tenant(MagicMock(), tenant_id)
        
        # Verify the name passed to internal provisioner
        # provision_tenant signature: (db, tenant_id, apps, existing, db_name)
        # It calls _provision_tenant(tenant_id, db_name)
        args, kwargs = mock_provision.call_args
        actual_tenant_id = args[0]
        actual_db_name = args[1]
        
        assert actual_tenant_id == tenant_id
        assert actual_db_name == f"tenant_{tenant_id}"
        assert re.match(r"^tenant_[a-zA-Z0-9_-]+$", actual_db_name)

def test_provision_tenant_custom_db_naming():
    """Assert custom DB name is preserved."""
    tenant_id = "test-tenant"
    custom_name = "my_custom_tenant_db"
    
    with patch("core.tenant.service._provision_tenant") as mock_provision:
        provision_tenant(MagicMock(), tenant_id, db_name=custom_name)
        
        args, kwargs = mock_provision.call_args
        assert args[1] == custom_name
