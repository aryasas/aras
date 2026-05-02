# -*- coding: utf-8 -*-
"""
arasCore/lib/workflow.py
State machine engine. Declarative workflow definitions attachable to any resource.

DB tables:
  wf_definition  — one workflow per resource type
  wf_state       — current state per object instance
  wf_history     — full transition history per object

Usage in manifest.py:
    from arasCore.lib.services.workflow import WorkflowDef, TransitionDef
    wf = WorkflowDef(
        name="invoice_workflow",
        resource_key="erp/acc_invoice",
        states=["draft", "pending", "posted", "cancelled"],
        initial="draft",
        transitions=[
            TransitionDef("submit",    "draft",    "pending",    roles=["accountant"]),
            TransitionDef("post",      "pending",  "posted",     roles=["manager"]),
            TransitionDef("cancel",    ["draft","pending"], "cancelled"),
        ],
    )
    register_workflow(wf)
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Callable

from flask_login import current_user

logger = logging.getLogger(__name__)

_workflow_registry: dict[str, "WorkflowDef"] = {}


@dataclass
class TransitionDef:
    action: str
    from_states: str | list[str]
    to_state: str
    roles: list[str] = field(default_factory=list)
    # Optional app-level permission hook: fn(user, obj) -> bool
    permission_hook: Callable | None = None

    def __post_init__(self):
        if isinstance(self.from_states, str):
            self.from_states = [self.from_states]


@dataclass
class WorkflowDef:
    name: str
    resource_key: str           # e.g. "erp/acc_invoice"
    states: list[str]
    initial: str
    transitions: list[TransitionDef]
    state_field: str = "state"  # column name on the model


def register_workflow(wf: WorkflowDef) -> None:
    _workflow_registry[wf.resource_key] = wf
    logger.info(f"[workflow] registered '{wf.name}' for '{wf.resource_key}'")


def get_workflow(resource_key: str) -> WorkflowDef | None:
    return _workflow_registry.get(resource_key)


# ── Two-stage transition checker ──────────────────────────────────────────────

def _stage1_framework_rbac(user, transition: TransitionDef) -> tuple[bool, str]:
    """Stage 1: framework-level role check via arasCore RBAC."""
    if not transition.roles:
        return True, ""
    if getattr(user, "is_admin", False):
        return True, ""
    from arasCore.permissions import UserRole, Role
    from arasCore.lib.core.extensions import db
    user_roles = (
        db.session.query(Role.slug)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user.id)
        .all()
    )
    user_role_slugs = {r[0] for r in user_roles}
    allowed = bool(user_role_slugs.intersection(set(transition.roles)))
    if not allowed:
        return False, f"Role required: {', '.join(transition.roles)}"
    return True, ""


def _stage2_app_hook(user, obj, transition: TransitionDef) -> tuple[bool, str]:
    """Stage 2: optional app-level permission hook."""
    if not transition.permission_hook:
        return True, ""
    try:
        ok = transition.permission_hook(user, obj)
        if not ok:
            return False, f"App permission denied for action '{transition.action}'"
        return True, ""
    except Exception as e:
        return False, str(e)


def can_transition(user, obj, action: str, wf: WorkflowDef) -> tuple[bool, str]:
    """Return (allowed, reason). Runs both RBAC stages."""
    current_state = getattr(obj, wf.state_field, wf.initial)
    tr = next((t for t in wf.transitions
               if t.action == action and current_state in t.from_states), None)
    if tr is None:
        return False, f"No transition '{action}' from state '{current_state}'"
    ok, msg = _stage1_framework_rbac(user, tr)
    if not ok:
        return False, msg
    return _stage2_app_hook(user, obj, tr)


def apply_transition(user, obj, action: str, wf: WorkflowDef,
                     note: str = "", db=None) -> dict:
    """
    Apply a workflow transition. Persists state + history.
    Returns {"ok": True, "state": new_state} or raises ValueError.
    """
    ok, reason = can_transition(user, obj, action, wf)
    if not ok:
        raise ValueError(reason)

    current_state = getattr(obj, wf.state_field, wf.initial)
    tr = next(t for t in wf.transitions
              if t.action == action and current_state in t.from_states)

    if db is None:
        from arasCore.lib.core.extensions import db as _db
        db = _db

    # Update object state
    setattr(obj, wf.state_field, tr.to_state)
    db.session.flush()

    # Upsert wf_state row
    from arasCore.lib.models.workflow_models import WfState, WfHistory
    state_row = WfState.query.filter_by(
        definition_name=wf.name,
        object_id=obj.id,
    ).first()
    if state_row:
        state_row.current_state = tr.to_state
        state_row.updated_by_id = getattr(user, "id", None)
    else:
        state_row = WfState(
            definition_name=wf.name,
            object_id=obj.id,
            current_state=tr.to_state,
            updated_by_id=getattr(user, "id", None),
        )
        db.session.add(state_row)

    # Append history
    db.session.add(WfHistory(
        definition_name=wf.name,
        object_id=obj.id,
        from_state=current_state,
        to_state=tr.to_state,
        action=action,
        user_id=getattr(user, "id", None),
        note=note or "",
    ))
    db.session.commit()

    try:
        from arasCore.lib.core.events import emit
        emit(f"{wf.resource_key}.state_changed", obj,
             action=action, from_state=current_state, to_state=tr.to_state)
    except Exception:
        pass

    return {"ok": True, "state": tr.to_state}


def get_available_actions(user, obj, wf: WorkflowDef) -> list[dict]:
    """Return list of transitions the current user can take from the current state."""
    current_state = getattr(obj, wf.state_field, wf.initial)
    result = []
    for tr in wf.transitions:
        if current_state not in tr.from_states:
            continue
        ok, _ = can_transition(user, obj, tr.action, wf)
        result.append({"action": tr.action, "to_state": tr.to_state, "allowed": ok})
    return result


def generate_mermaid(wf: WorkflowDef) -> str:
    """Generate Mermaid state diagram code for the workflow."""
    lines = ["stateDiagram-v2"]
    lines.append(f"    [*] --> {wf.initial}")
    
    # Track states to ensure all are included even if no transitions
    all_states = set(wf.states)
    
    for tr in wf.transitions:
        for from_state in tr.from_states:
            roles_str = f" [{', '.join(tr.roles)}]" if tr.roles else ""
            lines.append(f"    {from_state} --> {tr.to_state}: {tr.action}{roles_str}")
            all_states.add(from_state)
            all_states.add(tr.to_state)
            
    return "\n".join(lines)
