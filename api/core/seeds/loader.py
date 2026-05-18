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

    from core.registry.role import Role
    from core.registry.permission import Permission

    roles_created = 0
    perms_created = 0
    skipped = 0

    for role_def in roles_data:
        role = db.query(Role).filter(Role.name == role_def["name"]).first()
        if not role:
            role = Role(name=role_def["name"], description=role_def.get("description", ""))
            db.add(role)
            db.flush()
            roles_created += 1
            logger.info("Created role: %s", role.name)
        else:
            skipped += 1

        existing_perms = {
            (p.resource, p.action)
            for p in db.query(Permission).filter(Permission.role_id == role.id).all()
        }

        for perm_def in role_def.get("permissions", []):
            resource = perm_def["resource"]
            for action in perm_def["actions"]:
                if (resource, action) not in existing_perms:
                    db.add(Permission(role_id=role.id, resource=resource, action=action))
                    perms_created += 1

    db.commit()
    logger.info(
        "RBAC seed complete: %d roles created, %d permissions created, %d roles skipped",
        roles_created, perms_created, skipped,
    )
    return {"roles_created": roles_created, "permissions_created": perms_created, "skipped": skipped}


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
