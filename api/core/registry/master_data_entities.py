# claude-sonnet-4-6
"""
Populate the shared master-data registry from each installed app's declared
`master_data` entities.

Framework inversion: instead of core importing app models to register them
(a core↛apps violation), every app declares its shared entities on
`App.master_data`, and this loop reads them back generically. Core never names
an app or imports an app model — it only iterates the app registry the
discovery step already populated.
"""
from .master_data_registry import master_data_registry


def register_core_entities():
    """Register every installed app's declared master_data into the registry.

    Idempotent: registry.register_entity overwrites by key, so re-running on a
    reload is safe. Runs after discover_apps() has filled App._registry.
    """
    from core.base.app import App

    for app_cls in App._registry.values():
        for entity in getattr(app_cls, "master_data", []) or []:
            master_data_registry.register_entity(app_cls.app_name, entity)
