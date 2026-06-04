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
        """Lookup a section by its stored section key (e.g. 'core_config.numbering').

        Sections are stored as (app_name, section.key) where section.key already
        carries any app prefix, so we match on the second tuple element directly.
        Falls back to the legacy 'app_name.key' split for callers that pass a
        bare app-scoped key.
        """
        if "." not in full_key:
            return None
        for (app_name, key), entry in self._entries.items():
            if key == full_key:
                return entry
        # Legacy fallback: treat the leading segment as the app name.
        app_name, key = full_key.split(".", 1)
        return self.get(app_name, key)

    def all(self) -> List[T]:
        return list(self._entries.values())

    def by_app(self, app_name: str) -> List[T]:
        return [v for k, v in self._entries.items() if k[0] == app_name]

    def clear(self):
        with self._lock:
            self._entries.clear()
