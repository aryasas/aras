"""App-level seed registry — apps register their seed functions here."""
from typing import Callable
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

_seed_fns: list[Callable[[Session], None]] = []


# claude-sonnet-4-6
def register(fn: Callable[[Session], None]) -> Callable[[Session], None]:
    """Decorator/callable: register a seed function to run during bootstrap."""
    _seed_fns.append(fn)
    return fn


# claude-sonnet-4-6
def run_all(db: Session) -> None:
    for fn in _seed_fns:
        try:
            fn(db)
        except Exception as exc:
            logger.warning("Seed %s failed: %s", fn.__name__, exc)
