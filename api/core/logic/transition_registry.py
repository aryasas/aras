"""
Purpose: Registry for `@Aras.on_transition` callbacks fired by WorkflowManager.
Context: Lives alongside other framework primitives in `core/logic/`.
Impact: Lets app code declare side-effects (GL posting, stock movement, ...)
        on document state transitions without re-implementing the trigger.
"""
from typing import Any, Callable, Dict, List, Tuple, Type


class TransitionRegistry:
    """Maps (model_class, from_state, to_state) -> [callback, ...]."""

    _by_class: Dict[Type[Any], Dict[Tuple[str, str], List[Callable]]] = {}

    @classmethod
    def register(cls, model: Type[Any], from_: str, to: str, fn: Callable) -> None:
        bucket = cls._by_class.setdefault(model, {})
        bucket.setdefault((from_, to), []).append(fn)

    @classmethod
    def get(cls, model: Type[Any], from_: str, to: str) -> List[Callable]:
        # Walk MRO so callbacks registered on a base class also fire for subclasses.
        out: List[Callable] = []
        for ancestor in getattr(model, "__mro__", [model]):
            bucket = cls._by_class.get(ancestor)
            if not bucket:
                continue
            out.extend(bucket.get((from_, to), []))
        return out


def on_transition(model: Type[Any], from_: str, to: str) -> Callable:
    """
    Decorator: registers a callback for a (model, from, to) state transition.

    Usage:
        @Aras.on_transition(model=SalesInvoice, from_="Draft", to="Posted")
        def post_invoice(db, item, user, transition): ...
    """
    def _wrap(fn: Callable) -> Callable:
        TransitionRegistry.register(model, from_, to, fn)
        return fn
    return _wrap
