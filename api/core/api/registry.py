from fastapi import APIRouter
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..aras import Aras

router = APIRouter(tags=["Registry Management"])

@router.get("/apps")
async def get_registered_apps():
    """Returns all apps currently in memory registry."""
    from ..base.app import App
    return {name: app_cls.get_manifest() for name, app_cls in App._registry.items()}

@router.get("/models")
async def get_registered_models():
    """Returns all models currently in memory registry."""
    from ..base.model import Model
    return {name: str(cls) for name, cls in Model._registry.items()}

@router.get("/schemas")
async def get_registered_schemas():
    """Returns all schemas currently in memory registry."""
    from ..base.schema import Schema
    return {name: str(cls) for name, cls in Schema._registry.items()}

@router.get("/views")
async def get_registered_views():
    """Returns all views currently in memory registry."""
    from ..base.view import View
    return {name: str(cls) for name, cls in View._registry.items()}
