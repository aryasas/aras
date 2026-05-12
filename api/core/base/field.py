"""
Purpose: Provides a metadata-rich column helper for SQLAlchemy models.
Context: Used within Aras.Model to define schema with UI-level attributes.
Impact: Enables automatic form generation and validation in the frontend.
"""
from sqlalchemy.orm import mapped_column

def Field(*args, 
          label: str = None, 
          ui_type: str = "string", 
          read_only: bool = False, 
          hidden: bool = False, 
          searchable: bool = True, 
          **kwargs):
    """
    Standard SQLAlchemy mapped_column wrapper that injects UI metadata into the 'info' dict.
    
    Args:
        label: Human-readable name for the field.
        ui_type: Frontend component type (e.g., 'currency', 'date', 'image').
        read_only: If true, the GUI will disable editing.
        hidden: If true, the field won't show in standard forms/lists.
        searchable: If true, the field is indexed for global search.
    """
    if "info" not in kwargs:
        kwargs["info"] = {}

    kwargs["info"].update({
        "label": label,
        "ui_type": ui_type,
        "read_only": read_only,
        "hidden": hidden,
        "searchable": searchable
    })
    return mapped_column(*args, **kwargs)
