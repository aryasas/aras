from typing import Callable, Dict, Any, Type, Optional, List
from functools import wraps
from pydantic import BaseModel, create_model

# Dataclass to store action metadata
class ModelAction:
    def __init__(self, name: str, handler: Callable, permission: str, input_schema: Optional[Type[BaseModel]] = None, label: Optional[str] = None, icon: Optional[str] = None):
        self.name = name
        self.handler = handler
        self.permission = permission
        self.input_schema = input_schema
        self.label = label or name.replace("_", " ").title()
        self.icon = icon

def action(
    name: str, 
    permission: str, 
    input_schema: Optional[Type[BaseModel]] = None, 
    label: Optional[str] = None, 
    icon: Optional[str] = None
) -> Callable:
    """
    Decorator to register a method as a custom model action.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(instance, *args, **kwargs):
            return func(instance, *args, **kwargs)
        
        # Attach action metadata to the wrapped function
        if not hasattr(wrapper, "_aras_actions"):
            wrapper._aras_actions = []
        wrapper._aras_actions.append(
            ModelAction(name, func, permission, input_schema, label, icon)
        )
        return wrapper
    return decorator

def get_model_actions(model_class: Type[Any]) -> Dict[str, ModelAction]:
    """
    Retrieves all registered actions for a given model class.
    """
    actions = {}
    for name in dir(model_class):
        member = getattr(model_class, name)
        if callable(member) and hasattr(member, "_aras_actions"):
            for act in member._aras_actions:
                actions[act.name] = act
    return actions
