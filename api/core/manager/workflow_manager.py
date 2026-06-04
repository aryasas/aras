"""
Purpose: DB-driven workflow engine. Loads templates from DB; falls back to code-defined __transitions__.
Context: Level 3 Manager. Uses HandlerRegistry for side-effect execution.
Impact: Enables fully user-configurable state machines with auditable side-effects.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..manager.manager import Manager
from ..base.model import Model


class WorkflowManager(Manager):

    # DB-driven workflow models live in an app (config); resolve them by key so
    # core never imports the app. When no app provides them, DB templates are
    # absent and the engine falls back to code-defined __transitions__.
    @staticmethod
    def _wf_models():
        from core.service_registry import ServiceRegistry
        return (
            ServiceRegistry.get("WorkflowTemplate"),
            ServiceRegistry.get("WorkflowTransition"),
            ServiceRegistry.get("WorkflowState"),
        )

    @classmethod
    def _load_db_template(cls, db: Session, document_type: str):
        """Returns active WorkflowTemplate for this document_type, or None."""
        WorkflowTemplate, _, _ = cls._wf_models()
        if WorkflowTemplate is None:
            return None
        try:
            return db.query(WorkflowTemplate).filter(
                WorkflowTemplate.document_type == document_type,
                WorkflowTemplate.is_active == True,
            ).first()
        except Exception:
            return None

    @classmethod
    def get_available_actions(cls, item: Model, user: Any, db: Session = None) -> List[Dict[str, Any]]:
        current_state = getattr(item, "status", "Draft")

        if db:
            template = cls._load_db_template(db, item.__tablename__)
            if template:
                _, WorkflowTransition, WorkflowState = cls._wf_models()
                transitions = (
                    db.query(WorkflowTransition)
                    .join(WorkflowState, WorkflowTransition.from_state_id == WorkflowState.id)
                    .filter(
                        WorkflowTransition.template_id == template.id,
                        WorkflowState.name == current_state,
                    )
                    .order_by(WorkflowTransition.sequence)
                    .all()
                )
                from ..logic.permissions import RBAC
                result = []
                for t in transitions:
                    if t.permission and not user.is_admin:
                        if not RBAC.has_permission(db, user, item.__tablename__, t.permission):
                            continue
                    to_state = db.get(WorkflowState, t.to_state_id)
                    result.append({
                        "name": t.name,
                        "to": to_state.name if to_state else "",
                        "label": t.label,
                        "icon": t.icon,
                    })
                return result

        # Fallback: code-defined __transitions__
        if not hasattr(item, "__transitions__") or not hasattr(item, "status"):
            return []

        from ..logic.permissions import RBAC
        available = []
        for trans in item.__transitions__:
            if trans["from"] == current_state:
                permission = trans.get("permission")
                if permission and not user.is_admin:
                    if not RBAC.has_permission(None, user, item.__tablename__, permission):
                        continue
                available.append({
                    "name": trans.get("name", trans["to"]),
                    "to": trans["to"],
                    "label": trans.get("label", trans["to"]),
                    "icon": trans.get("icon", "ArrowRight"),
                })
        return available

    @classmethod
    def trigger_action(cls, db: Session, item: Model, action_name: str, user: Any) -> bool:
        current_state = getattr(item, "status", "Draft")

        template = cls._load_db_template(db, item.__tablename__)

        if template:
            _, WorkflowTransition, WorkflowState = cls._wf_models()
            transition_row = (
                db.query(WorkflowTransition)
                .join(WorkflowState, WorkflowTransition.from_state_id == WorkflowState.id)
                .filter(
                    WorkflowTransition.template_id == template.id,
                    WorkflowTransition.name == action_name,
                    WorkflowState.name == current_state,
                )
                .first()
            )
            if not transition_row:
                raise ValueError(f"Action '{action_name}' is not valid for state '{current_state}'")

            # Permission check
            from ..logic.permissions import RBAC
            if transition_row.permission and not user.is_admin:
                if not RBAC.has_permission(db, user, item.__tablename__, transition_row.permission):
                    raise PermissionError(f"Missing permission '{transition_row.permission}'")

            to_state = db.get(WorkflowState, transition_row.to_state_id)
            old_status = item.status
            item.status = to_state.name if to_state else item.status

            # Execute handler actions ordered by sequence
            from ..logic.handler_registry import HandlerRegistry
            for action in sorted(transition_row.actions, key=lambda a: a.sequence):
                fn = HandlerRegistry.resolve(action.handler_name)
                if fn is None:
                    raise RuntimeError(f"Handler '{action.handler_name}' not found in registry")
                try:
                    fn(db=db, item=item, params=action.params or {})
                except Exception as e:
                    item.status = old_status
                    raise RuntimeError(f"Handler '{action.handler_name}' failed: {e}") from e

            return True

        # Fallback: code-defined __transitions__ + TransitionRegistry callbacks
        transition = None
        for trans in getattr(item, "__transitions__", []):
            name = trans.get("name", trans["to"])
            if trans["from"] == current_state and name == action_name:
                transition = trans
                break

        if not transition:
            raise ValueError(f"Action '{action_name}' is not valid for state '{current_state}'")

        from ..logic.permissions import RBAC
        permission = transition.get("permission")
        if permission and not user.is_admin:
            if not RBAC.has_permission(db, user, item.__tablename__, permission):
                raise PermissionError(f"Missing permission '{permission}'")

        old_state = item.status
        item.status = transition["to"]

        from ..logic.transition_registry import TransitionRegistry
        for cb in TransitionRegistry.get(item.__class__, old_state, item.status):
            try:
                cb(db=db, item=item, user=user, transition=transition)
            except Exception as e:
                item.status = old_state
                raise RuntimeError(f"Callback {cb.__name__} failed: {e}") from e

        return True
