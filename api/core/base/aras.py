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
    def action(*args, **kwargs):
        from ..logic.model_actions import action
        return action(*args, **kwargs)

    @staticmethod
    def computed(*args, **kwargs):
        from .model import Model
        return Model.computed(*args, **kwargs)

