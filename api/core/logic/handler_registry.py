"""
Purpose: 2-layer workflow handler registry. Framework registers built-ins; apps can override by name.
Context: Used by WorkflowManager to execute side-effects on state transitions.
Impact: Decouples workflow logic from hardcoded callbacks.
"""
from typing import Callable, Optional


class HandlerRegistry:
    _handlers: dict[str, Callable] = {}
    _descriptions: dict[str, str] = {}

    @classmethod
    def register(cls, name: str, description: str = ""):
        """Decorator. App layer overrides framework handlers by registering with the same name."""
        def decorator(fn: Callable) -> Callable:
            cls._handlers[name] = fn
            cls._descriptions[name] = description
            return fn
        return decorator

    @classmethod
    def resolve(cls, name: str) -> Optional[Callable]:
        return cls._handlers.get(name)

    @classmethod
    def list_handlers(cls) -> list[dict]:
        return [{"name": k, "description": cls._descriptions.get(k, "")} for k in cls._handlers]
