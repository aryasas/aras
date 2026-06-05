import re

from core.tenant.registry import tenant_registry
from core.tenant.provisioner import provision_tenant as _provision_tenant
from core.tenant.provisioner import deprovision_tenant as _deprovision_tenant
from core.tenant.provisioner import seed_tenant as _seed_tenant
from core.tenant.provisioner import _validate_db_identifier

def list_tenants(db=None):
    return tenant_registry.list_all()


# claude-opus-4-8
def _slugify_db_name(tenant_id: str) -> str:
    """Build a safe default db_name from a tenant_id (lowercase, _-only)."""
    slug = re.sub(r"[^a-z0-9_]", "_", tenant_id.lower()).strip("_")[:55]
    if not slug or not slug[0].isalpha() and slug[0] != "_":
        slug = f"t_{slug}"
    return f"tenant_{slug}"[:63]

def provision_tenant(db, tenant_id: str, apps=("core_config",), existing=False, db_name=None):
    # Normalize default; validate any caller-supplied name early for a clean 400.
    db_name = db_name or _slugify_db_name(tenant_id)
    _validate_db_identifier(db_name)
    return _provision_tenant(tenant_id, db_name)

def delete_tenant(db, tenant_id: str):
    ok = _deprovision_tenant(tenant_id)
    if not ok:
        raise ValueError(f"Tenant '{tenant_id}' not found.")
    return True

def seed_tenant(db, tenant_id: str):
    return _seed_tenant(tenant_id)
