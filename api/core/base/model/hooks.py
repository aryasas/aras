import logging

class HookMixin:
    """Lifecycle hooks for Model."""

    def before_save(self, is_new: bool, db=None):
        """Generic hook executed before database commit."""
        pass
        
    def after_save(self, is_new: bool): 
        """Generic hook executed after database commit."""
        pass

    def _fire_hooks(self, hook_name: str):
        """Calls all methods on this instance decorated with @Aras.on_create/on_update/on_delete."""
        for name in dir(type(self)):
            method = getattr(type(self), name, None)
            if callable(method) and getattr(method, "_aras_hook", None) == hook_name:
                try:
                    getattr(self, name)()
                except Exception as e:
                    logging.error(f"[Model] Hook error in {self.__tablename__}.{name}: {e}")
