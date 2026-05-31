import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List, Type, Any, Optional
from pydantic import create_model

from ...base.router import Router
from ...lib.database import get_db
from ..permissions import check_permissions

from .helpers import _generate_pydantic_schemas
from .crud import register_crud_routes
from .bulk import register_bulk_routes
from .m2m import register_m2m_routes
from .aggregate import register_aggregate_routes
from .search import register_search_routes

class RouterFactory(Router):
    """
    Generic factory for generating standardized CRUD routes for any Aras Model.
    Supports Enterprise features: Pagination, Advanced Filtering, Global Search, and Bulk Actions.
    """

    @classmethod
    def create_router(cls, model_class: Type[Any], prefix: str = None) -> APIRouter:
        """
        Main entry point. Generates a fully-functional APIRouter for the given model.
        Automatically handles RBAC, Pydantic schemas, and scope filtering.
        """
        # ── 1. Initialization & Schemas ──────────────────────────────────────
        api_tag = getattr(model_class, "__app__", "Registry")
        router_prefix = prefix or f"/{model_class.__tablename__}"
        
        # gemini-pro: Get app for module protection
        from ...base.app import App
        app_cls = None
        for a in App._registry.values():
            if model_class in a.models:
                app_cls = a
                break
        
        allow_public = getattr(model_class, "__public__", False)
        saas_module = getattr(app_cls, "saas_module", "") if app_cls else ""

        # Plan-gate the entire router when the model is NOT public.
        # For __public__ models (e.g. landing/CMS reads) we leave reads open and
        # apply the guard per-write-route inside register_crud_routes.
        dependencies = []
        if saas_module and not allow_public:
            from ...auth.module_guard import require_module  # lazy: avoids core↔apps.saas circular import
            dependencies.append(Depends(require_module(saas_module)))

        router = APIRouter(prefix=router_prefix, tags=[api_tag], dependencies=dependencies)

        Schema, PatchSchema = _generate_pydantic_schemas(model_class)

        # When the router is NOT blanket-gated but app declares a saas_module,
        # writes must still be plan-gated. Pass the module down so crud.py can
        # attach per-write dependencies.
        write_saas_module = saas_module if (saas_module and allow_public) else ""

        # ── 2. Register Specialized Routes ───────────────────────────────────
        register_crud_routes(router, model_class, Schema, PatchSchema, allow_public, api_tag, write_saas_module=write_saas_module)
        register_bulk_routes(router, model_class)
        register_m2m_routes(router, model_class)
        register_aggregate_routes(router, model_class, allow_public)
        register_search_routes(router, model_class, allow_public)

        # ── 3. Custom Model Actions ──────────────────────────────────────────
        for action_name, model_action in model_class._actions.items():
            # Create a dynamic Pydantic model for the action's input if schema is provided
            ActionSchema = model_action.input_schema

            def make_action_route(name, action_func, schema_cls=None):
                perm = action_func.permission or "edit"
                rbac_action = "UPDATE" if perm in ["edit", "update", "write"] else perm.upper()
                
                # Use /action/name to avoid collision with /{item_id}
                @router.post(f"/{{item_id}}/action/{name}")
                def execute_action(
                    item_id: int,
                    request: Request,
                    payload: Optional[dict] = None,
                    db: Session = Depends(get_db),
                    user: Any = Depends(check_permissions(model_class.__tablename__, rbac_action))
                ):
                    item = model_class.get(db, item_id)
                    if not item:
                        from ...exceptions import ResourceNotFoundException
                        raise ResourceNotFoundException("Item not found")
                    
                    from .helpers import _check_scope_ownership
                    _check_scope_ownership(model_class, request, item)
                    
# gemini-flash
                    # Pass db and arguments from payload
                    args = payload or {}
                    
                    import inspect
                    sig = inspect.signature(action_func.handler)
                    call_args = {"db": db, **args}
                    if "current_user" in sig.parameters:
                        call_args["current_user"] = user
                    
                    result = action_func.handler(item, **call_args)
                    db.commit()
                    return result
                return execute_action

            make_action_route(action_name, model_action, ActionSchema)

        return router
