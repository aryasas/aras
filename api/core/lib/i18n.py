from typing import Dict, Any, Optional
import json
import os
from ..base.service import Service
from sqlalchemy.orm import Session

# Direct imports of models to prevent circular dependencies with Aras facade
from ..registry.translation_model import TranslationModel
from ..registry.app_model import AppModel
from ..registry.resource_model import ResourceModel
from ..registry.field_model import FieldModel

class TranslationService(Service):
    """
    Manages loading and retrieving translations for the Aras framework.
    Translations are primarily loaded from the database registry.
    """
    _translations_cache: Dict[str, Dict[str, str]] = {} # {lang_code: {key: value}}

    @classmethod
    def load_translations_from_db(cls, db: Session, lang_code: str) -> None:
        """Loads translations for a given language from the database registry."""
        if lang_code in cls._translations_cache:
            return

        translations_map = {}
        
        # Fetch all translations for the given language code
        db_translations = db.query(TranslationModel).filter(
            TranslationModel.language_code == lang_code
        ).all()

        # Optimize by pre-fetching related names to avoid N+1 queries
        app_names = {app.id: app.name for app in db.query(AppModel).all()}
        resource_names = {res.id: res.name for res in db.query(ResourceModel).all()}
        # For fields, we need both field name and its parent resource name
        field_details = {
            f.id: (f.name, resource_names.get(f.resource_id)) 
            for f in db.query(FieldModel).all()
        }

        for t in db_translations:
            key_parts = []
            if t.registry_type == 'app' and t.registry_id in app_names:
                app_name = app_names[t.registry_id]
                key_parts = ['app', app_name, t.property_name]
            elif t.registry_type == 'resource' and t.registry_id in resource_names:
                resource_name = resource_names[t.registry_id]
                key_parts = ['resource', resource_name, t.property_name]
            elif t.registry_type == 'field' and t.registry_id in field_details:
                field_name, resource_name = field_details[t.registry_id]
                if resource_name: # Ensure resource name was found
                    key_parts = ['field', resource_name, field_name, t.property_name]
            else:
                # Fallback for general translations not linked to specific registry item by ID
                # Or for cases where registry_id lookup failed (e.g., deleted item)
                # Or generic registry_type.property_name
                key_parts = [t.registry_type, t.property_name]

            if key_parts:
                full_key = ".".join(key_parts)
                translations_map[full_key] = t.translated_value
        
        cls._translations_cache[lang_code] = translations_map

    @classmethod
    def get_translation(
        cls, 
        key: str, 
        lang_code: Optional[str] = None, 
        db: Optional[Session] = None
    ) -> str:
        """
        Retrieves a translation for a given key and language code.
        If not found, returns the key itself.
        """
        if not lang_code:
            return key # No language specified, return key

        if lang_code not in cls._translations_cache and db:
            cls.load_translations_from_db(db, lang_code)
        
        return cls._translations_cache.get(lang_code, {}).get(key, key)

    @classmethod
    def translate_metadata_dict(cls, metadata: Dict[str, Any], lang: str, db: Session) -> Dict[str, Any]:
        """Translates a metadata dictionary using loaded translations."""
        if not lang:
            return metadata

        cls.load_translations_from_db(db, lang) # Ensure translations are loaded

        # Translate resource title
        if "title" in metadata:
            # Use the resource name for constructing the translation key
            resource_name = metadata.get("resource")
            if resource_name:
                metadata["title"] = cls.get_translation(f"resource.{resource_name}.title", lang, db)

        # Translate field labels
        for field_meta in metadata.get("fields", []):
            field_name = field_meta["name"]
            resource_name = metadata.get("resource") # Get resource name from metadata
            if resource_name and field_name:
                # Prioritize specific field.label (e.g., field.resource_name.field_name.label)
                translated_label = cls.get_translation(f"field.{resource_name}.{field_name}.label", lang, db)
                if translated_label == f"field.{resource_name}.{field_name}.label": # If not found, use fallback
                    # Fallback to a less specific key (e.g., field.field_name.label - assuming registry_type='field', property_name='field_name.label'
                    # which is not what TranslationModel supports directly based on current structure.)
                    # Let's adjust this for clarity: The previous fallback was incorrect.
                    # It should be: if the specific field label isn't found, keep the original label.
                    # The UIGenerator already sets a default label from column.info or title case.
                    # So, if get_translation returns the key itself, it means no translation is found,
                    # and the original label should be retained.
                    pass # Keep the original label if no translation found.
                else:
                    field_meta["label"] = translated_label
            # If no resource_name or field_name, or if not translated, original label is kept.

        return metadata
