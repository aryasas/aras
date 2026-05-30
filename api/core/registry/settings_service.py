# gemini-flash
from typing import Any, Optional, Dict
import json
import logging
from sqlalchemy.orm import Session
from .sys_settings import Settings
from .config_registry import config_registry, ConfigField, ConfigSection

logger = logging.getLogger(__name__)

class SettingsService:
    _cache: Dict[tuple[str, str], Any] = {}

    @classmethod
    def get(cls, db: Session, namespace: str, key: str, default: Any = None) -> Any:
        cache_key = (namespace, key)
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        # 1. Check registry for schema and default
        field_def = cls._get_field_def(namespace, key)
        
        # 2. Check DB for override
        row = db.query(Settings).filter_by(namespace=namespace, key=key).first()
        
        if row:
            value = cls._cast_value(row.value, field_def.type if field_def else row.value_type)
        elif field_def:
            value = field_def.default
        else:
            value = default

        cls._cache[cache_key] = value
        return value

    @classmethod
    def set(cls, db: Session, namespace: str, key: str, value: Any, user_id: int = None) -> Settings:
        field_def = cls._get_field_def(namespace, key)
        
        if field_def and field_def.validator:
            if not field_def.validator(value):
                raise ValueError(f"Validation failed for setting {namespace}.{key}")

        if isinstance(value, (list, dict)):
            str_value = json.dumps(value)
        else:
            str_value = str(value)
            
        value_type = field_def.type if field_def else "str"
        is_secret = field_def.secret if field_def else False

        row = db.query(Settings).filter_by(namespace=namespace, key=key).first()
        if row:
            row.value = str_value
            row.value_type = value_type
            row.is_secret = is_secret
            row.updated_by = user_id
        else:
            row = Settings(
                namespace=namespace,
                key=key,
                value=str_value,
                value_type=value_type,
                is_secret=is_secret,
                updated_by=user_id
            )
            db.add(row)
        
        db.commit()
        cls.invalidate_cache(namespace, key)
        
        if field_def:
            # Find section for write_hook
            section = cls._get_section_for_field(namespace, key)
            if section and section.write_hook:
                section.write_hook(db, namespace, key, value, user_id)
        
        return row

    @classmethod
    def all(cls, db: Session, namespace: str, reveal_secrets: bool = False) -> dict:
        # Get all sections for this namespace
        sections = config_registry.by_app(namespace)
        result = {}
        
        # 1. Fill with defaults from registry
        for section in sections:
            section_data = {}
            for field in section.fields:
                val = field.default
                if field.secret and not reveal_secrets:
                    val = "***"
                section_data[field.key] = val
            result[section.key] = section_data
            
        # 2. Overlay with DB values
        rows = db.query(Settings).filter_by(namespace=namespace).all()
        for row in rows:
            # Find which section this key belongs to
            section_key = None
            field_def = None
            for section in sections:
                for f in section.fields:
                    if f.key == row.key:
                        section_key = section.key
                        field_def = f
                        break
                if section_key: break
            
            if section_key:
                val = cls._cast_value(row.value, field_def.type)
                if field_def.secret and not reveal_secrets:
                    val = "***"
                result[section_key][row.key] = val
                
        return result

    @classmethod
    def bulk_set(cls, db: Session, namespace: str, values: dict, user_id: int = None):
        # values shape: {section_key: {field_key: value, ...}, ...}
        for section_key, section_values in values.items():
            # Validate section exists for this namespace
            # (In practice, set() will just work even if not in registry)
            for field_key, value in section_values.items():
                cls.set(db, namespace, field_key, value, user_id)

    @classmethod
    def schema(cls, namespace: str) -> dict:
        sections = config_registry.by_app(namespace)
        return {
            "namespace": namespace,
            "sections": [
                {
                    "key": s.key,
                    "label": s.label,
                    "icon": s.icon,
                    "fields": [
                        {
                            "key": f.key,
                            "type": f.type,
                            "label": f.label,
                            "help": f.help,
                            "secret": f.secret,
                            "choices": f.choices
                        } for f in s.fields
                    ]
                } for s in sections
            ]
        }

    @classmethod
    def invalidate_cache(cls, namespace: str, key: str = None):
        if key:
            cls._cache.pop((namespace, key), None)
        else:
            keys_to_remove = [k for k in cls._cache.keys() if k[0] == namespace]
            for k in keys_to_remove:
                del cls._cache[k]

    @staticmethod
    def _get_field_def(namespace: str, key: str) -> Optional[ConfigField]:
        sections = config_registry.by_app(namespace)
        for s in sections:
            for f in s.fields:
                if f.key == key:
                    return f
        return None

    @staticmethod
    def _get_section_for_field(namespace: str, key: str) -> Optional[ConfigSection]:
        sections = config_registry.by_app(namespace)
        for s in sections:
            for f in s.fields:
                if f.key == key:
                    return s
        return None

    @staticmethod
    def _cast_value(value: str, value_type: str) -> Any:
        if value is None: return None
        if value_type == "number":
            try: 
                return float(value) if "." in value else int(value)
            except: 
                return value
        if value_type == "bool":
            return value.lower() in ("true", "1", "yes")
        if value_type == "list" or value_type == "dict":
            try: 
                return json.loads(value)
            except: 
                return value
        return value
