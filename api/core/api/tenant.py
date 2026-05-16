from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from core.auth.service import get_current_user
from core.tenant.registry import tenant_registry
from core.tenant.provisioner import provision_tenant, deprovision_tenant, seed_tenant

router = APIRouter(tags=["Tenant Management"])


class ProvisionRequest(BaseModel):
    tenant_id: str
    db_name: Optional[str] = None


@router.get("/tenants")
def list_tenants(current_user=Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only.")
    return {"data": tenant_registry.list_all()}


@router.post("/tenants/provision", status_code=201)
def provision(body: ProvisionRequest, current_user=Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only.")
    db_name = body.db_name or f"aras_tenant_{body.tenant_id}"
    try:
        info = provision_tenant(body.tenant_id, db_name)
        return {"success": True, "data": info}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tenants/{tenant_id}/seed")
def seed(tenant_id: str, current_user=Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only.")
    try:
        result = seed_tenant(tenant_id)
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tenants/{tenant_id}")
def deprovision(tenant_id: str, current_user=Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only.")
    ok = deprovision_tenant(tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Tenant '{tenant_id}' not found.")
    return {"success": True, "message": f"Tenant '{tenant_id}' deprovisioned."}
