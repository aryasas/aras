"""
Purpose: Exposes Aras Registry models through the standard RouterFactory.
Context: Level 3 API. Enables administrative control over framework metadata.
Impact: Provides endpoints for RBAC, Audit, and Resource management.
"""
from fastapi import APIRouter
from core import Aras

router = APIRouter(prefix="/registry", tags=["Framework Registry"])

# Expose standard registry models using the automated RouterFactory
router.include_router(Aras.Router(Aras.ActivityLog))
router.include_router(Aras.Router(Aras.Role))
router.include_router(Aras.Router(Aras.Permission))
router.include_router(Aras.Router(Aras.User))
router.include_router(Aras.Router(Aras.UserRole))
router.include_router(Aras.Router(Aras.ArasSetting))
router.include_router(Aras.Router(Aras.AppModel))
router.include_router(Aras.Router(Aras.ResourceModel))
router.include_router(Aras.Router(Aras.FieldModel))
router.include_router(Aras.Router(Aras.LinkModel))
