"""@require_perm — check ErpPermission via ErpUserCompany."""
from functools import wraps
from flask import abort, g
from flask_login import current_user


def require_perm(perm_code: str):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.is_admin:
                return f(*args, **kwargs)
            company_id = getattr(g, "current_company_id", None)
            if not _user_has_perm(current_user.id, perm_code, company_id):
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator


def _user_has_perm(user_id: int, perm_code: str, company_id: int = None) -> bool:
    from aras.erp.erp_core.models.acl import ErpUserCompany, ErpRolePermission, ErpPermission
    memberships = ErpUserCompany.query.filter_by(user_id=user_id)
    if company_id:
        memberships = memberships.filter_by(company_id=company_id)
    for uc in memberships:
        if not uc.role_id:
            continue
        has = (
            ErpRolePermission.query
            .join(ErpPermission, ErpPermission.id == ErpRolePermission.permission_id)
            .filter(
                ErpRolePermission.role_id == uc.role_id,
                ErpPermission.code == perm_code,
            ).first()
        )
        if has:
            return True
    return False
