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

    # Keep aliases for backward compatibility but mark as deprecated if possible
    # For now, let's just rename them to avoid the warning.
    # We will update the one usage found.

