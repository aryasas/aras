# gemini-flash
import pytest
from sqlalchemy.orm import Session
from core.registry.config_registry import config_registry, ConfigSection, ConfigField
from core.lib.config import config
from core.registry.config_value import ConfigValue, ConfigValueAudit

def test_config_registry_registration():
    config_registry.clear()
    section = ConfigSection(
        key="test.section",
        label="Test Section",
        fields=[ConfigField(key="name", type="string", default="test_val")]
    )
    config_registry.register_section("test_app", section)
    
    assert config_registry.get_by_full_key("test.section") == section
    assert len(config_registry.all()) == 1

def test_config_service_set_get(db: Session):
    config_registry.clear()
    section = ConfigSection(
        key="test.section",
        label="Test Section",
        fields=[ConfigField(key="name", type="string", default="default")]
    )
    config_registry.register_section("test_app", section)
    
    # Test default
    assert config.get(db, "test.section.name") == "default"
    
    # Test set
    config.set(db, "test.section.name", "new_val", user_id=1)
    db.commit()
    
    # Cache should be invalidated and return new val
    assert config.get(db, "test.section.name") == "new_val"
    
    # Verify DB
    val_row = db.query(ConfigValue).filter_by(scope_key="test.section", field_key="name").first()
    assert val_row.value_json == "new_val"
    
    # Verify Audit
    audit_row = db.query(ConfigValueAudit).filter_by(scope_key="test.section", field_key="name").first()
    assert audit_row.new_value == "new_val"
    assert audit_row.user_id == 1

def test_config_service_secret(db: Session):
    config_registry.clear()
    section = ConfigSection(
        key="test.secrets",
        label="Secrets",
        fields=[ConfigField(key="api_key", type="secret", secret=True)]
    )
    config_registry.register_section("test_app", section)
    
    secret_val = "super-secret-123"
    config.set(db, "test.secrets.api_key", secret_val)
    db.commit()
    
    # GET should return plaintext if using the service (decrypted)
    assert config.get(db, "test.secrets.api_key") == secret_val
    
    # DB should be encrypted
    val_row = db.query(ConfigValue).filter_by(scope_key="test.secrets", field_key="api_key").first()
    assert val_row.value_json != secret_val
    assert len(val_row.value_json) > 20 # encrypted string is long
    
    # Audit should be masked
    audit_row = db.query(ConfigValueAudit).filter_by(scope_key="test.secrets", field_key="api_key").first()
    assert audit_row.new_value == "••••"
