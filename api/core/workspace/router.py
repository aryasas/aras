# gemini-flash
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session
from core.tenant.router import get_db
from core.auth.service import get_current_user
from core.auth.models import User
from core.registry.config_registry import config_registry
from core.registry.config_value import ConfigValue
from core.lib.config import config
from core.lib.secrets import mask

router = APIRouter(prefix="/settings", tags=["Settings"])


def _has_stored_value(value: Any) -> bool:
    return value not in (None, "", [], {})


def _section_complete(db: Session, section_key: str) -> bool:
    section = config_registry.get_by_full_key(section_key)
    if not section:
        return False

    stored_values = {
        row.field_key: row.value_json
        for row in db.query(ConfigValue).filter(ConfigValue.scope_key == section_key).all()
    }
    required_fields = [field for field in section.fields if getattr(field, "required", False)]

    if required_fields:
        return all(_has_stored_value(stored_values.get(field.key)) for field in required_fields)

    return any(_has_stored_value(value) for value in stored_values.values())

@router.get("/sections")
def get_sections(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Filter visible sections by permission if needed
    # For now, return all non-hidden
    all_sections = config_registry.all()
    result = []
    for s in sorted(all_sections, key=lambda x: x.order):
        if not s.hidden:
            result.append({
                "key": s.key,
                "label": s.label,
                "icon": s.icon,
                "scope": s.scope
            })
    return result


@router.get("/setup")
def get_setup_steps(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    _ = getattr(request.state, "org_id", 0)
    sections = [
        section
        for section in config_registry.all()
        if section.setup_step is not None
    ]
    result = []
    for section in sorted(sections, key=lambda item: item.setup_step or 0):
        result.append({
            "key": section.key,
            "label": section.label,
            "icon": section.icon,
            "setup_step": section.setup_step,
            "complete": _section_complete(db, section.key),
        })
    return result

@router.get("/sections/{key}")
def get_section_details(
    key: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    section = config_registry.get_by_full_key(key)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    # Get current values
    values = config.bulk_get(db, key)
    
    # Mask secrets
    can_read_secrets = True # TODO: Check permission config.secrets.read
    
    fields = []
    for f in section.fields:
        val = values.get(f"{key}.{f.key}", f.default)
        if f.secret and not can_read_secrets:
            val = mask(val)
        elif f.secret and val:
            val = mask(val) # Always mask in GET unless rotating/revealing
            
        fields.append({
            "key": f.key,
            "type": f.type,
            "label": f.label or f.key.title(),
            "help": f.help,
            "choices": f.choices,
            "secret": f.secret,
            "value": val
        })
    
    return {
        "key": section.key,
        "label": section.label,
        "fields": fields
    }

@router.put("/sections/{key}")
def update_section(
    key: str,
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    section = config_registry.get_by_full_key(key)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    for field_key, value in data.items():
        full_key = f"{key}.{field_key}"
        try:
            config.set(db, full_key, value, user_id=user.id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    db.commit()
    return {"success": True, "message": f"Section {key} updated."}

@router.post("/sections/{key}/rotate-secret/{field}")
def rotate_secret(
    key: str,
    field: str,
    value: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # TODO: Verify permission config.write
    full_key = f"{key}.{field}"
    try:
        config.set(db, full_key, value, user_id=user.id)
        db.commit()
        return {"success": True, "message": f"Secret {field} updated."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
