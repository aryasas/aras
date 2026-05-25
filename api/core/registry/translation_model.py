"""
Purpose: DB model for storing UI-level translations for Registry objects.
Context: Part of Aras.Registry namespace.
Impact: Enables multi-language support for App labels, Resource titles, and Field labels.
"""
from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from ..base.model import Model

class TranslationModel(Model):
    """
    Stores localized strings for framework metadata.
    Mappings: (registry_type, registry_id, language_code, property_name) -> translated_value
    """
    __tablename__ = "translations"

    # 'app', 'resource', 'field'
    registry_type: Mapped[str] = mapped_column(String(20), index=True) 
    
    # ID of the record in AppModel, ResourceModel, or FieldModel
    registry_id: Mapped[int] = mapped_column(Integer, index=True)
    
    # 'en', 'es', 'fr', etc.
    language_code: Mapped[str] = mapped_column(String(10), index=True) 
    
    # 'label', 'description', 'title', 'placeholder'
    property_name: Mapped[str] = mapped_column(String(50), index=True) 
    
    translated_value: Mapped[str] = mapped_column(Text)
