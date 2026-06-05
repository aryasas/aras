"""
Purpose: Provides a metadata-rich column helper for SQLAlchemy models.
Context: Used within Aras.Model to define schema with UI-level attributes.
Impact: Enables automatic form generation and validation in the frontend.
"""
from sqlalchemy.orm import mapped_column

# gpt-5
def Field(*args,
          label: str = None,
          ui_type: str = None,
          read_only: bool = False,
          hidden: bool = False,
          pii: bool = False,
          searchable: bool = True,
          link_column: str = None,
          display_column: str = None,
          min_length: int = None,
          max_length: int = None,
          min_value: float = None,
          max_value: float = None,
          pattern: str = None,
          **kwargs):
    """
    Standard SQLAlchemy mapped_column wrapper that injects UI metadata into the 'info' dict.

    Args:
        label: Human-readable name for the field.
        ui_type: Frontend component type (e.g., 'currency', 'date', 'image').
        read_only: If true, the GUI will disable editing.
        hidden: If true, the field won't show in standard forms/lists.
        pii: If true, audit/storage paths can treat the field as personal data.
        searchable: If true, the field is indexed for global search.
        link_column: For lookups, the target field (usually 'id').
        display_column: For lookups, the target field to display (e.g., 'name').
        min_length: Minimum string length for server + client validation.
        max_length: Maximum string length for server + client validation.
        min_value: Minimum numeric value for server + client validation.
        max_value: Maximum numeric value for server + client validation.
        pattern: Regex pattern string for server + client validation.
    """
    if "info" not in kwargs:
        kwargs["info"] = {}

    ui_meta = {
        "label": label,
        "ui_type": ui_type,
        "read_only": read_only,
        "hidden": hidden,
        "pii": pii,
        "searchable": searchable,
        "link_column": link_column,
        "display_column": display_column,
        "min_length": min_length,
        "max_length": max_length,
        "min_value": min_value,
        "max_value": max_value,
        "pattern": pattern,
    }
    # Only update info with non-None values so that .get("key", fallback) works
    kwargs["info"].update({k: v for k, v in ui_meta.items() if v is not None})

    return mapped_column(*args, **kwargs)
