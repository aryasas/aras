from unittest.mock import MagicMock, patch

import pytest

from core.tenant.provisioner import _validate_db_identifier, provision_tenant


# gpt-5
@pytest.mark.parametrize(
    "name",
    [
        'x"; DROP DATABASE y; --',
        "x' OR '1'='1",
        "1abc",
        "Foo",
        "",
        "a" * 64,
        "a-b",
    ],
)
def test_validate_db_identifier_rejects_unsafe_values(name: str):
    with pytest.raises(ValueError):
        _validate_db_identifier(name)


# gpt-5
@pytest.mark.parametrize("name", ["tenant_acme", "t_123", "_x"])
def test_validate_db_identifier_accepts_safe_values(name: str):
    assert _validate_db_identifier(name) == name


# gpt-5
def test_provision_tenant_rejects_malicious_db_name_before_sql_execution():
    conn = MagicMock()
    admin_engine = MagicMock()
    admin_engine.connect.return_value.__enter__.return_value = conn

    with patch("core.tenant.provisioner.tenant_registry.get", return_value=None), patch(
        "core.tenant.provisioner._get_admin_connection", return_value=admin_engine
    ):
        with pytest.raises(ValueError):
            provision_tenant("tenant-acme", 'x"; DROP DATABASE y; --')

    conn.execute.assert_not_called()
