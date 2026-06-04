"""
RBAC seed loader — reads YAML or JSON, creates roles + permissions idempotently.

Usage:
    from core.seeds.loader import load_rbac
    load_rbac(Path(__file__).parent / "rbac_framework.yaml", db)
"""
import json
import logging
from pathlib import Path
from typing import Union

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def load_rbac(path: Union[str, Path], db: Session) -> dict:
    """Load roles and permissions from a YAML or JSON seed file.

    Returns counts: {"roles_created": N, "permissions_created": N, "skipped": N}
    """
    path = Path(path)
    data = _parse(path)
    roles_data = data.get("roles", [])

    roles_created = 0
    perms_created = 0
    skipped = 0

    for role_def in roles_data:
        # Idempotently ensure role exists and has perms
        created, perms = upsert_permissions(
            db, 
            role_def["name"], 
            permissions=[(p["resource"], p["actions"]) for p in role_def.get("permissions", [])],
            description=role_def.get("description", "")
        )
        if created:
            roles_created += 1
        else:
            skipped += 1
        perms_created += perms

    db.commit()
    logger.info(
        "RBAC seed complete: %d roles created, %d permissions created, %d roles skipped",
        roles_created, perms_created, skipped,
    )
    return {"roles_created": roles_created, "permissions_created": perms_created, "skipped": skipped}


def upsert_permissions(db: Session, role_name: str, resource: str = None, actions: list[str] = None, permissions: list = None, description: str = "") -> tuple[bool, int]:
    """# claude-opus-4-8
    Idempotently ensure a role exists and has the given (resource, action) perms.
    Can be called with a single resource/actions pair, or a list of (resource, actions) tuples.
    Returns (created, perms_count).
    """
    from core.registry.role import Role
    from core.registry.permission import Permission

    role = db.query(Role).filter(Role.name == role_name).first()
    created = False
    if not role:
        role = Role(name=role_name, description=description)
        db.add(role)
        db.flush()
        created = True
        logger.info("Created role: %s", role.name)

    existing_perms = {
        (p.resource, p.action)
        for p in db.query(Permission).filter(Permission.role_id == role.id).all()
    }

    perms_created = 0
    
    # Normalize inputs
    perm_list = permissions or []
    if resource and actions:
        perm_list.append((resource, actions))
    
    for res, acts in perm_list:
        for action in acts:
            if (res, action) not in existing_perms:
                db.add(Permission(role_id=role.id, resource=res, action=action))
                perms_created += 1
                
    return created, perms_created


def _parse(path: Path) -> dict:
    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        import yaml
        with open(path) as f:
            return yaml.safe_load(f)
    if suffix == ".json":
        with open(path) as f:
            return json.load(f)
    raise ValueError(f"Unsupported seed format: {suffix} (use .yaml or .json)")
