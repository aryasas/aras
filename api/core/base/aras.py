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
    def computed_field(func):
        """Decorator to mark a method as a serializable computed field."""
        func._aras_computed = True
        return func

    # claude-opus-4-7
    @staticmethod
    def on_create(fn):
        """
        Decorator — marks a method as an on_create hook.
        Called after a new record is committed. Signature: (self, db=None, user_id=None) -> None.
        """
        fn._aras_hook = "on_create"
        return fn

    # claude-opus-4-7
    @staticmethod
    def on_update(fn):
        """
        Decorator — marks a method as an on_update hook.
        Called after an existing record is committed. Signature: (self, db=None, user_id=None) -> None.
        """
        fn._aras_hook = "on_update"
        return fn

    # claude-opus-4-7
    @staticmethod
    def on_delete(fn):
        """
        Decorator — marks a method as an on_delete hook.
        Called just before deletion / soft-delete. Signature: (self, db=None, user_id=None) -> None.
        """
        fn._aras_hook = "on_delete"
        return fn

    # claude-opus-4-7
    @staticmethod
    def on_validate(fn):
        """
        Decorator — marks a method as an on_validate hook.
        Runs pre-commit; may raise ValidationException to abort save.
        Signature: (self, db=None, user_id=None) -> None.
        """
        fn._aras_hook = "on_validate"
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
        from ..lib.numbering import SeriesManager
        return SeriesManager.get_next(db, key, prefix)

    # Keep aliases for backward compatibility but mark as deprecated if possible
    # For now, let's just rename them to avoid the warning.
    # We will update the one usage found.

