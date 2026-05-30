# gemini-flash
from dataclasses import dataclass
from typing import List, Optional, Type
from .base_registry import Registry

@dataclass
class MasterEntity:
    key: str                          # stable id, e.g. "currency"
    model: Type                       # SQLAlchemy model class
    label: str = ""                   # human label; auto-derived from model if empty
    icon: str = "Database"            # lucide icon name
    scope: str = "module"             # "shared" | "module" | "feature"
    order: int = 100
    hidden: bool = False
    help: str = ""
    app_name: str = ""                # Injected during registration

class MasterDataRegistry(Registry[MasterEntity]):
    def register_entity(self, app_name: str, entity: MasterEntity):
        entity.app_name = app_name
        if not entity.label and hasattr(entity.model, "__name__"):
            entity.label = entity.model.__name__
        self.register(app_name, entity.key, entity)

    def by_scope(self, scope: str) -> List[MasterEntity]:
        return sorted(
            [e for e in self.all() if e.scope == scope],
            key=lambda x: (x.order, x.label)
        )

    def get_by_key(self, key: str) -> Optional[MasterEntity]:
        for entity in self.all():
            if entity.key == key:
                return entity
        return None

master_data_registry = MasterDataRegistry()
