from core.tenant.registry import tenant_registry
from core.tenant.provisioner import provision_tenant as _provision_tenant
from core.tenant.provisioner import deprovision_tenant as _deprovision_tenant
from core.tenant.provisioner import seed_tenant as _seed_tenant

def list_tenants(db=None):
    return tenant_registry.list_all()

def provision_tenant(db, tenant_id: str, apps=("core_config",), existing=False, db_name=None):
    db_name = db_name or f"tenant_{tenant_id}"
    return _provision_tenant(tenant_id, db_name)

def delete_tenant(db, tenant_id: str):
    ok = _deprovision_tenant(tenant_id)
    if not ok:
        raise ValueError(f"Tenant '{tenant_id}' not found.")
    return True

def seed_tenant(db, tenant_id: str):
    return _seed_tenant(tenant_id)
