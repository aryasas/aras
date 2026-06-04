# gemini-flash
import json
import logging
from typing import Any, Optional, Dict
from sqlalchemy.orm import Session
from threading import Lock

from ..registry.config_registry import config_registry
from ..registry.config_value import ConfigValue, ConfigValueAudit
from .secrets import encrypt, decrypt

logger = logging.getLogger(__name__)

class ConfigService:
    _cache: Dict[str, Dict[str, Any]] = {} # tenant_id -> {key: value}
    _lock = Lock()

    @classmethod
    def _get_tenant_id(cls, db: Session) -> str:
        try:
            url = str(db.get_bind().url)
            # Remove query params if any
            if "?" in url:
                url = url.split("?")[0]
            db_name = url.split("/")[-1]
            if db_name.startswith("tenant_"):
                return db_name.removeprefix("tenant_")
            # Legacy fallback — remove after 2026-08
            if db_name.startswith("aras_tenant_"):
                return db_name.removeprefix("aras_tenant_")
            return db_name
        except Exception:
            return "global"

    @classmethod
    def _get_cache(cls, tenant_id: str) -> Dict[str, Any]:
        with cls._lock:
            if tenant_id not in cls._cache:
                cls._cache[tenant_id] = {}
            return cls._cache[tenant_id]

    @classmethod
    def get(cls, db: Session, key: str, default: Any = None) -> Any:
        tenant_id = cls._get_tenant_id(db)
        cache = cls._get_cache(tenant_id)
        
        if key in cache:
            return cache[key]

        section_key, field_key = cls._split_key(key)
        val_row = db.query(ConfigValue).filter_by(scope_key=section_key, field_key=field_key).first()
        
        value = None
        is_secret = False
        
        # Find field definition for default and secret check
        section = config_registry.get_by_full_key(section_key)
        target_field = None
        if section:
            for f in section.fields:
                if f.key == field_key:
                    target_field = f
                    is_secret = f.secret
                    break

        if not val_row:
            value = target_field.default if target_field else default
        else:
            value = val_row.value_json
            if is_secret and value:
                value = decrypt(value, tenant_id)

        cache[key] = value
        return value

    @classmethod
    def set(cls, db: Session, key: str, value: Any, user_id: int = None):
        tenant_id = cls._get_tenant_id(db)
        section_key, field_key = cls._split_key(key)
        
        section = config_registry.get_by_full_key(section_key)
        if not section:
            raise ValueError(f"Config section '{section_key}' not registered.")
        
        target_field = None
        for f in section.fields:
            if f.key == field_key:
                target_field = f
                break

        # Dynamic sections (e.g. core_config.numbering) accept arbitrary field keys
        # whose values are supplied at runtime and have no predeclared ConfigField.
        if not target_field and not getattr(section, "dynamic", False):
            raise ValueError(f"Field '{field_key}' not found in section '{section_key}'.")

        if target_field and target_field.validator and not target_field.validator(value):
            raise ValueError(f"Validation failed for config '{key}'.")

        is_secret = bool(target_field and target_field.secret)
        stored_value = value
        if is_secret and value and value != "••••":
            stored_value = encrypt(value, tenant_id)

        val_row = db.query(ConfigValue).filter_by(scope_key=section_key, field_key=field_key).first()
        old_value = None
        
        if val_row:
            old_value = val_row.value_json
            if value == "••••" and is_secret:
                # Don't overwrite with mask
                pass
            else:
                val_row.value_json = stored_value
        else:
            if value == "••••" and is_secret:
                stored_value = ""
            val_row = ConfigValue(scope_key=section_key, field_key=field_key, value_json=stored_value)
            db.add(val_row)

        # Record audit
        audit = ConfigValueAudit(
            scope_key=section_key,
            field_key=field_key,
            old_value=old_value if not is_secret else "••••",
            new_value=stored_value if not is_secret else "••••",
            user_id=user_id
        )
        db.add(audit)
        
        # Trigger write hook if present
        if section.write_hook:
            section.write_hook(db, key, value, user_id)

        # Invalidate cache
        cache = cls._get_cache(tenant_id)
        if key in cache:
            del cache[key]
        
        return True

    @classmethod
    def flag(cls, db: Session, key: str, default: bool = False) -> bool:
        val = cls.get(db, key, default)
        return bool(val)

    @classmethod
    def bulk_get(cls, db: Session, section_prefix: str) -> Dict[str, Any]:
        tenant_id = cls._get_tenant_id(db)
        rows = db.query(ConfigValue).filter(ConfigValue.scope_key.startswith(section_prefix)).all()
        
        result = {}
        for r in rows:
            full_key = f"{r.scope_key}.{r.field_key}"
            value = r.value_json
            
            # Check if secret
            section = config_registry.get_by_full_key(r.scope_key)
            if section:
                for f in section.fields:
                    if f.key == r.field_key and f.secret and value:
                        value = decrypt(value, tenant_id)
                        break
            result[full_key] = value
            
        # Merge with defaults for missing keys
        section = config_registry.get_by_full_key(section_prefix)
        if section:
            for f in section.fields:
                full_key = f"{section_prefix}.{f.key}"
                if full_key not in result:
                    result[full_key] = f.default
                    
        return result

    @staticmethod
    def _split_key(key: str):
        if key.count(".") < 2:
            parts = key.split(".")
            if len(parts) == 2:
                return parts[0], parts[1]
            return "core", key
        parts = key.rsplit(".", 1)
        return parts[0], parts[1]

config = ConfigService
