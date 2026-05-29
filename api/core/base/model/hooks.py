import inspect
import logging

from core.exceptions import ValidationException


# claude-opus-4-7
class HookMixin:
    """Lifecycle hooks for Model."""

    def before_save(self, is_new: bool, db=None):
        """Generic hook executed before database commit."""
        pass

    def after_save(self, is_new: bool):
        """Generic hook executed after database commit."""
        pass

    # claude-opus-4-7
    def _fire_hooks(self, hook_name: str, db=None, user_id=None):
        """
        Calls all methods on this instance decorated with @Aras.on_create/on_update/on_delete/on_validate.
        Passes db and user_id to hooks that accept them (introspected via signature).
        ValidationException from on_validate propagates to abort save.
        """
        for name in dir(type(self)):
            method = getattr(type(self), name, None)
            if not callable(method) or getattr(method, "_aras_hook", None) != hook_name:
                continue
            bound = getattr(self, name)
            try:
                params = inspect.signature(bound).parameters
                kwargs = {}
                if "db" in params:
                    kwargs["db"] = db
                if "user_id" in params:
                    kwargs["user_id"] = user_id
                bound(**kwargs)
            except ValidationException:
                raise
            except Exception as e:
                logging.error(f"[Model] Hook error in {self.__tablename__}.{name}: {e}")
