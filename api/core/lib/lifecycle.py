# claude-sonnet-4-6
"""
Optional cross-app lifecycle dispatch (Tier 0 — pure, no framework imports).

Problem this solves: an app (e.g. POS) emits lifecycle side-effects ("post the
journal", "move the stock") that are *implemented by other apps* (accounting,
stock). Those apps may not be installed — on a free plan, POS runs without
accounting or stock. The emitting app must NOT crash when a consumer is absent.

This module provides the generic resolve-and-dispatch logic. The framework
supplies the actual resolver (a name -> callable lookup) and an optional
"is this effect required here" predicate; this layer stays dependency-free so
it is reusable by any app, in any product built on the framework.
"""
from dataclasses import dataclass
from typing import Callable, Optional, Any, Dict, List


@dataclass(frozen=True)
class Effect:
    """One named side-effect an app emits during a lifecycle transition.

    required=False (default): if no consumer is registered, silently skip.
    required=True: if no consumer is registered, raise — the effect is
    mandatory in this context and a missing consumer is a real error.
    """
    name: str
    required: bool = False
    params: Optional[Dict] = None


class MissingEffectConsumer(Exception):
    """Raised only when a required Effect has no registered consumer."""
    def __init__(self, name: str):
        self.name = name
        super().__init__(
            f"Required lifecycle effect '{name}' has no registered consumer. "
            f"Install the app that provides it, or mark the effect optional."
        )


# claude-sonnet-4-6
def dispatch(
    effects: List[Effect],
    resolver: Callable[[str], Optional[Callable]],
    *,
    context: Any = None,
    db: Any = None,
) -> Dict[str, str]:
    """Resolve and run each effect's consumer if present.

    resolver(name) -> callable | None. Returns a per-effect outcome map
    ("ran" | "skipped") so callers can report what actually happened —
    useful for "posted invoice (journal skipped: accounting not installed)".

    Graceful degradation is the whole point: optional effects with no
    consumer are skipped, not fatal. Only required effects raise.
    """
    outcome: dict[str, str] = {}
    for eff in effects:
        fn = resolver(eff.name)
        if fn is None:
            if eff.required:
                raise MissingEffectConsumer(eff.name)
            outcome[eff.name] = "skipped"
            continue
        fn(db=db, item=context, params=eff.params or {})
        outcome[eff.name] = "ran"
    return outcome
