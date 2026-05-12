"""
Purpose: Provides a metadata-rich column helper for SQLAlchemy models.
Context: Used within Aras.Model to define schema with UI-level attributes.
Impact: Enables automatic form generation and validation in the frontend.
"""
from sqlalchemy.orm import mapped_column

def Field(*args,
          label: str = None,
          ui_type: str = None,
          read_only: bool = False,
          hidden: bool = False,
          searchable: bool = True,
          link_column: str = None,
          display_column: str = None,
          **kwargs):
    """
    Standard SQLAlchemy mapped_column wrapper that injects UI metadata into the 'info' dict.

    Args:
        label: Human-readable name for the field.
        ui_type: Frontend component type (e.g., 'currency', 'date', 'image').
        read_only: If true, the GUI will disable editing.
        hidden: If true, the field won't show in standard forms/lists.
        searchable: If true, the field is indexed for global search.
        link_column: For lookups, the target field (usually 'id').
        display_column: For lookups, the target field to display (e.g., 'name').
    """
    if "info" not in kwargs:
        kwargs["info"] = {}

    ui_meta = {
        "label": label,
        "ui_type": ui_type,
        "read_only": read_only,
        "hidden": hidden,
        "searchable": searchable,
        "link_column": link_column,
        "display_column": display_column
    }
    # Only update info with non-None values so that .get("key", fallback) works
    kwargs["info"].update({k: v for k, v in ui_meta.items() if v is not None})
    
    return mapped_column(*args, **kwargs)
