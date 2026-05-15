"""
Purpose: Request-scoped tenant/company/workspace primitive used by `__scoped_by__`.
Context: Resolved from the JWT `scope` claim and surfaced as `request.state.scope`.
Impact: RouterFactory uses this to filter list/get queries and inject scope on writes.
"""
from typing import Any, Dict, Optional


class ScopeContext:
    """Lightweight bag of scope key→value pairs for the current request."""

    def __init__(self, values: Optional[Dict[str, Any]] = None):
        self.values: Dict[str, Any] = dict(values or {})

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def as_dict(self) -> Dict[str, Any]:
        return dict(self.values)

    def __bool__(self) -> bool:
        return bool(self.values)

    def __repr__(self) -> str:
        return f"ScopeContext({self.values!r})"


def scope_from_user(user: Any) -> ScopeContext:
    """
    Build a default scope from user attributes. Looks for `current_company_id`
    on the user; subclasses / future extensions can layer on more keys.
    """
    values: Dict[str, Any] = {}
    if user is not None:
        cid = getattr(user, "current_company_id", None)
        if cid is not None:
            values["company_id"] = cid
    return ScopeContext(values)
