import json
import os
from threading import RLock
from typing import Dict, Any, Optional, List

# Default path for the registry file, can be overridden by environment variables
DEFAULT_REGISTRY_PATH = os.path.join("data", "tenant_registry.json")


class TenantRegistry:
    """
    Manages the persistence and retrieval of tenant information.

    This implementation uses a JSON file as the backing store. It is thread-safe
    through the use of an RLock to serialize access to the file.
    The path to the registry file can be configured via the `TENANT_REGISTRY_PATH`
    environment variable.
    """

    _instance: Optional["TenantRegistry"] = None
    _lock = RLock()

    def __init__(self, registry_path: Optional[str] = None):
        if not TenantRegistry._instance:
            self.registry_path = (
                registry_path
                or os.getenv("TENANT_REGISTRY_PATH")
                or DEFAULT_REGISTRY_PATH
            )
            self._tenants: Dict[str, Dict[str, Any]] = self._load()
            TenantRegistry._instance = self

    @classmethod
    def get_instance(cls) -> "TenantRegistry":
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = cls()
        return cls._instance

    def _load(self) -> Dict[str, Dict[str, Any]]:
        """Loads tenant data from the JSON file."""
        with self._lock:
            try:
                os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
                with open(self.registry_path, "r") as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return {}

    def _save(self):
        """Saves the current tenant data to the JSON file."""
        with self._lock:
            with open(self.registry_path, "w") as f:
                json.dump(self._tenants, f, indent=4)

    def register(
        self, tenant_id: str, db_url: str, meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Registers a new tenant or updates an existing one.

        Args:
            tenant_id: The unique identifier for the tenant.
            db_url: The database connection URL for the tenant.
            meta: Optional dictionary for additional metadata.

        Returns:
            The full record of the registered tenant.
        """
        with self._lock:
            tenant_data = {"tenant_id": tenant_id, "db_url": db_url, "meta": meta or {}}
            self._tenants[tenant_id] = tenant_data
            self._save()
            return tenant_data

    def get(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a tenant's information by their ID.

        Args:
            tenant_id: The ID of the tenant to retrieve.

        Returns:
            A dictionary containing the tenant's data, or None if not found.
        """
        with self._lock:
            # Perform a fresh load to ensure we have the latest data if file is edited externally
            self._tenants = self._load()
            return self._tenants.get(tenant_id)

    def unregister(self, tenant_id: str) -> bool:
        """
        Removes a tenant from the registry.

        Args:
            tenant_id: The ID of the tenant to remove.

        Returns:
            True if the tenant was found and removed, False otherwise.
        """
        with self._lock:
            if tenant_id in self._tenants:
                del self._tenants[tenant_id]
                self._save()
                return True
            return False

    def list_all(self) -> List[Dict[str, Any]]:
        """
        Lists all registered tenants.

        Returns:
            A list of dictionaries, where each dictionary represents a tenant.
        """
        with self._lock:
            self._tenants = self._load()
            return list(self._tenants.values())


# Singleton instance for easy access
tenant_registry = TenantRegistry.get_instance()
