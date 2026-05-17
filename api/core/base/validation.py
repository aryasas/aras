"""
Purpose: Level 2 Base Validation class for Pydantic request/response schemas.
Context: Inherits from Aras (Level 1) and Pydantic BaseModel.
Impact: Ensures all data validation logic is rooted in the Aras framework.
"""
from typing import Dict, Type, List, Optional, Any
from pydantic import BaseModel, Field as PydanticField, field_validator, model_validator, ConfigDict
from .aras import Aras


class Validation(Aras, BaseModel):
    """
    Level 2 Core Validation.
    Inherits from Aras (Level 1).
    Base for all API request and response validation models.
    """
    __abstract__ = True
    _registry: Dict[str, Type['Validation']] = {}

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='before')
    @classmethod
    def _empty_str_to_none(cls, values: Any) -> Any:
        if isinstance(values, dict):
            return {k: (None if v == '' else v) for k, v in values.items()}
        return values


class ColumnDefinition(Validation):
    name: str
    label: Optional[str] = None
    field_type: str = "string"
    required: bool = False
    relation_table: Optional[str] = None
    read_only: bool = False
    hidden: bool = False
    searchable: bool = True


class TableDefinition(Validation):
    name: str
    title: Optional[str] = None
    columns: List[ColumnDefinition]


class AppDefinition(Validation):
    name: str
    label: Optional[str] = None
    description: Optional[str] = ""
    icon: Optional[str] = "Package"
    version: Optional[str] = "1.0.0"


class ManifestDefinition(Validation):
    app: AppDefinition
    tables: List[TableDefinition] = []

    @field_validator("app")
    @classmethod
    def validate_app_name(cls, v):
        if not v.name.replace("_", "").replace("-", "").isalnum():
            raise ValueError("App name must be alphanumeric (underscores and hyphens allowed)")
        return v
