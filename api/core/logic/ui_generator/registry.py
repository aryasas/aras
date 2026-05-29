# claude-opus-4-7
from typing import Any, Callable, Dict, Optional, Tuple

TypeHandler = Callable[[Any], Optional[Tuple[str, Optional[list]]]]

_TYPE_HANDLERS: Dict[str, TypeHandler] = {}

def register_handler(name: str):
    def decorator(func: TypeHandler):
        _TYPE_HANDLERS[name] = func
        return func
    return decorator

def get_handlers():
    return _TYPE_HANDLERS
