# claude-opus-4-8
"""Workspace config endpoints — static option catalogs consumed by form pickers.

Lives in core/workspace (framework tier) because unit_type is a core Organization
concept; keeping it here avoids any apps/* dependency from the Organization form.
"""
from fastapi import APIRouter

from .models import UNIT_TYPE_OPTIONS

config_router = APIRouter()


# claude-opus-4-8
@config_router.get("/unit-types")
def get_unit_types() -> list[dict[str, str]]:
    """Canonical org unit-type options for the unit_type_picker combobox."""
    return UNIT_TYPE_OPTIONS
