"""
Purpose: Level 2 Base Validation class for Pydantic request/response schemas.
Context: Inherits from Aras (Level 1) and Pydantic BaseModel.
Impact: Ensures all data validation logic is rooted in the Aras framework.
"""
from typing import Dict, Type
from pydantic import BaseModel
from .aras import Aras

class Validation(Aras, BaseModel):
    """
    Level 2 Core Validation.
    Inherits from Aras (Level 1).
    Base for all API request and response validation models.
    """
    __abstract__ = True
    _registry: Dict[str, Type['Validation']] = {}

    class Config:
        from_attributes = True
