# gemini-flash
from dataclasses import dataclass
from typing import List, Optional, Any
from .base_registry import Registry

@dataclass
class MenuEntry:
    key: str
    label: str
    icon: str = "Circle"
    route: Optional[str] = None
    order: int = 100
    parent: Optional[str] = None
    app: str = ""
    required_perm: Optional[str] = None

class MenuRegistry(Registry[MenuEntry]):
    """Registry for menu entries."""
    
    def register_from_manifest(self, app_name: str, manifest: dict):
        entries = manifest.get("menu_entries", [])
        for entry in entries:
            if isinstance(entry, dict):
                entry_obj = MenuEntry(
                    key=entry["key"],
                    label=entry["label"],
                    icon=entry.get("icon", "Circle"),
                    route=entry.get("route"),
                    order=entry.get("order", 100),
                    parent=entry.get("parent"),
                    app=app_name,
                    required_perm=entry.get("required_perm")
                )
                self.register(app_name, entry_obj.key, entry_obj)
            elif isinstance(entry, MenuEntry):
                entry.app = app_name
                self.register(app_name, entry.key, entry)

# Singleton instance
menu_registry = MenuRegistry()
