# gemini-flash
from dataclasses import dataclass
from typing import List, Optional
from .base_registry import Registry

@dataclass
class Permission:
    key: str
    label: str
    app: str = ""
    description: str = ""

class PermissionRegistry(Registry[Permission]):
    """Registry for permissions."""
    
    def register_from_manifest(self, app_name: str, manifest: dict):
        permissions = manifest.get("permissions", [])
        for perm in permissions:
            if isinstance(perm, dict):
                perm_obj = Permission(
                    key=perm["key"],
                    label=perm["label"],
                    app=app_name,
                    description=perm.get("description", "")
                )
                self.register(app_name, perm_obj.key, perm_obj)
            elif isinstance(perm, Permission):
                perm.app = app_name
                self.register(app_name, perm.key, perm)

# Singleton instance
permission_registry = PermissionRegistry()
