# gemini-flash
import threading
from typing import Generic, TypeVar, Dict, List, Optional, Any

T = TypeVar('T')

class Registry(Generic[T]):
    """
    Generic thread-safe registry for framework components.
    Keyed by (app_name, key).
    """
    def __init__(self):
        self._entries: Dict[tuple[str, str], T] = {}
        self._lock = threading.RLock()

    def register(self, app_name: str, key: str, entry: T):
        with self._lock:
            self._entries[(app_name, key)] = entry

    def unregister(self, app_name: str):
        with self._lock:
            keys_to_remove = [k for k in self._entries.keys() if k[0] == app_name]
            for k in keys_to_remove:
                del self._entries[k]

    def get(self, app_name: str, key: str) -> Optional[T]:
        return self._entries.get((app_name, key))

    def get_by_full_key(self, full_key: str) -> Optional[T]:
        """Lookup by 'app_name.key' string."""
        if "." not in full_key:
            return None
        app_name, key = full_key.split(".", 1)
        return self.get(app_name, key)

    def all(self) -> List[T]:
        return list(self._entries.values())

    def by_app(self, app_name: str) -> List[T]:
        return [v for k, v in self._entries.items() if k[0] == app_name]

    def clear(self):
        with self._lock:
            self._entries.clear()
