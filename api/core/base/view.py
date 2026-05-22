"""
Purpose: Level 2 Base View class for UI configuration.
Context: Decouples UI metadata from SQLAlchemy models.
Impact: Allows developers to customize forms/lists without changing DB models.
"""
import copy
import re
from typing import Dict, Any, Type, Optional
from .aras import Aras
from ..logic.ui_generator import UIGenerator

class View(Aras):
    """
    Base View class for defining UI metadata.
    Developers can inherit from this to override auto-generated defaults.
    """
    __abstract__ = True
    _view_map: Dict[str, Type['View']] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls.__dict__.get("__abstract__"):
            if hasattr(cls, 'model') and cls.model is not None:
                View._view_map[cls.model.__tablename__] = cls
                # Auto-derive title from model class name if not explicitly set on this subclass
                if not cls.__dict__.get("title"):
                    name = cls.model.__name__
                    for suffix in ("Model", "View"):
                        if name.endswith(suffix):
                            name = name[:-len(suffix)]
                            break
                    cls.title = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', name)

    @classmethod
    def _auto_register(cls, model_class: Type) -> Type['View']:
        """Ensure a model has a View entry, creating a minimal auto-View if needed."""
        tablename = model_class.__tablename__
        if tablename not in cls._view_map:
            type(f"{model_class.__name__}View", (cls,), {"model": model_class})
        return cls._view_map[tablename]

    model: Type['Aras.Model'] = None
    title: Optional[str] = None
    icon: Optional[str] = None
    standalone: bool = False  # child models with standalone=True appear in app menu
    fields: Dict[str, Dict[str, Any]] = {}
    layout: Optional[list] = None

    @classmethod
    def get_for_model(cls, model_class: Type['Aras.Model']) -> Optional[Type['View']]:
        return cls._view_map.get(model_class.__tablename__)

    @classmethod
    def render_metadata(cls, db: Any = None, lang: Optional[str] = None) -> Dict[str, Any]:
        """Generates metadata, applying View-level overrides to the generated defaults."""
        metadata = UIGenerator.generate_metadata(cls.model, db=db, lang=lang)

        # Override with custom view settings
        if cls.title:
            metadata["title"] = cls.title
        if cls.icon:
            metadata["icon"] = cls.icon
        
        # Apply field overrides
        if cls.fields:
            for field_meta in metadata["fields"]:
                if field_meta["name"] in cls.fields:
                    field_meta.update(cls.fields[field_meta["name"]])
        
        if cls.layout:
            layout = copy.deepcopy(cls.layout)
            # Inject scope fields (e.g. org_id) into the first section if missing from all sections
            scoped_by = getattr(cls.model, "__scoped_by__", None) or []
            scope_field_names = [pair[0] for pair in scoped_by]
            if scope_field_names:
                def _section_fields(s):
                    direct = s.get("fields", [])
                    from_tabs = [f for tab in s.get("tabs", []) for f in tab.get("fields", [])]
                    return direct + from_tabs
                def _field_name(f):
                    return f if isinstance(f, str) else f.get("field", "")
                all_layout_fields = {_field_name(f) for s in layout for f in _section_fields(s)}
                missing = [sf for sf in scope_field_names if sf not in all_layout_fields]
                if missing and layout and "fields" in layout[0]:
                    layout[0]["fields"] = missing + list(layout[0]["fields"])
            metadata["layout"] = layout
        else:
            # Auto-generate layout from field-level tab/section metadata
            tabs_map = {} # tab_name -> {section_name -> [field_names]}
            default_sections = {} # section_name -> [field_names]
            section_props = {} # (tab_name, section_name) -> {"foldable": bool, "default_folded": bool}
            standalone_fields = []

            for f in metadata["fields"]:
                if f.get("hidden") or f.get("form_hidden"):
                    continue
                tab_name = f.get("tab")
                section_name = f.get("section") or ""
                
                # Collect section properties
                prop_key = (tab_name, section_name)
                if prop_key not in section_props:
                    section_props[prop_key] = {"foldable": False, "default_folded": False}
                if f.get("foldable"):
                    section_props[prop_key]["foldable"] = True
                if f.get("default_folded"):
                    section_props[prop_key]["default_folded"] = True

                if tab_name:
                    if tab_name not in tabs_map:
                        tabs_map[tab_name] = {}
                    if section_name not in tabs_map[tab_name]:
                        tabs_map[tab_name][section_name] = []
                    tabs_map[tab_name][section_name].append(f["name"])
                elif section_name:
                    if section_name not in default_sections:
                        default_sections[section_name] = []
                    default_sections[section_name].append(f["name"])
                else:
                    standalone_fields.append(f["name"])

            generated_layout = []
            
            # 1. Main sections (no tab)
            for s_name, f_names in default_sections.items():
                props = section_props.get((None, s_name), {})
                generated_layout.append({
                    "title": s_name,
                    "fields": f_names,
                    "type": "section",
                    "foldable": props.get("foldable", False),
                    "default_folded": props.get("default_folded", False)
                })
            
            # 2. Tabs
            if tabs_map:
                tab_entries = []
                for t_name, sections in tabs_map.items():
                    for s_name, s_f_names in sections.items():
                        props = section_props.get((t_name, s_name), {})
                        tab_entries.append({
                            "title": f"{t_name} - {s_name}" if s_name else t_name,
                            "fields": s_f_names,
                            "type": "tab",
                            "foldable": props.get("foldable", False),
                            "default_folded": props.get("default_folded", False)
                        })
                
                if tab_entries:
                    generated_layout.append({
                        "type": "tabs",
                        "tabs": tab_entries
                    })

            # 3. Catch-all for standalone fields if no layout was generated yet
            if not generated_layout and standalone_fields:
                generated_layout.append({
                    "title": "General",
                    "fields": standalone_fields,
                    "type": "section"
                })
            elif standalone_fields:
                # Add to the first section or create a new one
                if generated_layout and "fields" in generated_layout[0]:
                    generated_layout[0]["fields"] = standalone_fields + generated_layout[0]["fields"]
                else:
                    generated_layout.insert(0, {
                        "title": "General",
                        "fields": standalone_fields,
                        "type": "section"
                    })

            if generated_layout:
                metadata["layout"] = generated_layout

        return metadata
