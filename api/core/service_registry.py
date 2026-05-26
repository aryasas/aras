"""
Service Registry for Aras Framework.
Centralizes access to services and models to prevent circular imports.
"""
import logging
from typing import Any, Optional

class ServiceRegistry:
    _registry = {}
    _resource_paths = {}

    @classmethod
    def register(cls, name: str, obj: any):
        """Register a service or model."""
        cls._registry[name] = obj
        logging.debug(f"Registered service: {name}")

    @classmethod
    def get(cls, name: str) -> any:
        """Retrieve a service or model by name."""
        return cls._registry.get(name)

    @classmethod
    def register_resource_path(cls, tablename: str, path: str):
        """Register the REST API path for a resource table."""
        cls._resource_paths[tablename] = path

    @classmethod
    def get_resource_path(cls, tablename: str) -> Optional[str]:
        """Retrieve the REST API path for a resource table."""
        return cls._resource_paths.get(tablename)

    @classmethod
    def clear(cls):
        """Clear the registry."""
        cls._registry = {}
        cls._resource_paths = {}
