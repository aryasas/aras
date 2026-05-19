"""
Purpose: The Level 1 foundational root class for the Aras Framework.
Context: Inherited by all Level 2 core classes (Model, App, Manager, Validation).
Impact: Provides a common type root and identity for all framework components.
"""

class Aras:
    """
    Level 1 Root Class.
    All framework components must inherit from this class directly (Level 2)
    or indirectly (Level 3+).
    """
    @staticmethod
    def model_action(*args, **kwargs):
        from ..logic.model_actions import action
        return action(*args, **kwargs)

    @staticmethod
    def computed_field(*args, **kwargs):
        from .model import Model
        return Model.computed_field(*args, **kwargs)

    @staticmethod
    def on_create(fn):
        """
        Decorator — marks a method as an on_create hook.
        The method is called after a new record is committed. Signature: (self) -> None.
        """
        fn._aras_hook = "on_create"
        return fn

    @staticmethod
    def on_update(fn):
        """
        Decorator — marks a method as an on_update hook.
        The method is called after an existing record is committed. Signature: (self) -> None.
        """
        fn._aras_hook = "on_update"
        return fn

    @staticmethod
    def on_delete(fn):
        """
        Decorator — marks a method as an on_delete hook.
        The method is called just before deletion / soft-delete. Signature: (self) -> None.
        """
        fn._aras_hook = "on_delete"
        return fn

    @staticmethod
    def on_transition(model, from_: str, to: str):
        """
        Decorator — registers a workflow transition callback.
        Callback signature: (db, item, user, transition) -> None.
        """
        from ..logic.transition_registry import on_transition as _t
        return _t(model, from_, to)

    @staticmethod
    def next_number(db, key: str, prefix: str = ""):
        """Helper to generate the next sequential number for a naming series."""
        from ..manager.naming_manager import SeriesManager
        return SeriesManager.get_next(db, key, prefix)

    # Keep aliases for backward compatibility but mark as deprecated if possible
    # For now, let's just rename them to avoid the warning.
    # We will update the one usage found.

